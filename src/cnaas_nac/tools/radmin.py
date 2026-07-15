import asyncio
from asyncio.subprocess import Process

from pydantic import BaseModel, IPvAnyNetwork, ValidationError
from pydantic_extra_types.mac_address import MacAddress
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.settings import settings
from cnaas_nac.models.radiusadminevent import RadiusAdminEvent, RadiusCommand

logger = get_logger()


class ClearClientPayload(BaseModel):
    network: IPvAnyNetwork


class DebugPayload(BaseModel):
    mac: MacAddress


async def radmin_setup() -> Process:
    proc = await asyncio.create_subprocess_exec(
        "radmin",
        "-f",
        "/var/run/radiusd/radiusd.sock",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if proc.stdout is not None:
        try:
            await proc.stdout.readuntil(b"radmin> ")
        except asyncio.exceptions.IncompleteReadError:
            raise RuntimeError("radmin stream closed before banner was received.")
    else:
        raise RuntimeError("Failed to read radmin banner")

    return proc


async def send_radmin_command(
    proc: Process, lock: asyncio.Lock, command: str
) -> list[str]:
    async with lock:
        if proc.stdin is None or proc.stdout is None:
            raise RuntimeError("Process streams are not available.")

        proc.stdin.write(f"{command}\n".encode("utf-8"))
        await proc.stdin.drain()

        try:
            raw_output = await proc.stdout.readuntil(b"radmin> ")
        except asyncio.exceptions.IncompleteReadError as e:
            # If the process closes (e.g., upon "terminate"), we capture what we can
            raw_output = e.partial

        output_str = raw_output.decode("utf-8")
        lines = output_str.strip().split("\n")

        # Remove the command echo and the prompt
        return lines[1:-1] if len(lines) > 1 else lines


async def radius_clear_client(
    proc: Process, lock: asyncio.Lock, raw_payload: dict
) -> None:
    data = ClearClientPayload(**raw_payload)

    if data.network.num_addresses > 4098:
        logger.info(
            f"Network {data.network} has more than 4098 addresses. Terminating radius service"
        )
        await send_radmin_command(proc, lock, "terminate")
        logger.info("Executed radmin terminate.")
    else:
        for ip in data.network.hosts():
            await send_radmin_command(proc, lock, f"del client ipaddr {ip}")
            logger.info(f"Cleared client {ip}")

    logger.info(f"Cleared network {data.network}")


async def radius_debug_start(
    proc: Process, lock: asyncio.Lock, raw_payload: dict
) -> None:
    data = DebugPayload(**raw_payload)

    output_lines = await send_radmin_command(proc, lock, "show debug condition")
    pre_conditions = None

    if output_lines:
        if f'&Calling-Station-Id == "{data.mac}"' in output_lines:
            logger.info(f"Debug condition for {data.mac} already exists.")
            return
        pre_conditions = output_lines[0].strip()

    if pre_conditions:
        debug_condition = f'{pre_conditions} || &Calling-Station-Id == "{data.mac}"'
    else:
        debug_condition = f'&Calling-Station-Id == "{data.mac}"'

    await send_radmin_command(proc, lock, f"debug condition '{debug_condition}'")
    logger.info(f"Started debug trace for {data.mac}")


async def radius_debug_stop(proc: Process, lock: asyncio.Lock) -> None:
    await send_radmin_command(proc, lock, "debug condition")
    await send_radmin_command(proc, lock, "debug level 0")
    logger.info("Stopped debug trace")


async def execute_radius_command(
    proc: Process, lock: asyncio.Lock, command: RadiusCommand, raw_payload: dict
) -> None:
    try:
        if command == RadiusCommand.CLEAR_CLIENT:
            await radius_clear_client(proc, lock, raw_payload)

        elif command == RadiusCommand.DEBUG_START:
            await radius_debug_start(proc, lock, raw_payload)

        elif command == RadiusCommand.DEBUG_STOP:
            await radius_debug_stop(proc, lock)

    except ValidationError as e:
        logger.error(f"Payload validation failed for '{command}': {e}")
    except Exception as e:
        logger.error(f"Execution failed for '{command}': {e}")


engine = create_async_engine(f"{settings.POSTGRES_ASYNC_PREFIX}{settings.POSTGRES_URI}")
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def run_worker() -> None:
    logger.info("Starting CNaaS NAC radmin sidecar...")
    last_checked = None

    while True:
        try:
            logger.info("Setting up radmin session")
            proc = await radmin_setup()
            radmin_lock = asyncio.Lock()

            logger.info("Setting up database session")
            async with AsyncSessionLocal() as session:
                while True:
                    if proc.returncode is not None:
                        logger.error("radmin subprocess died. Restarting connection...")
                        break

                    if last_checked is None:
                        last_checked = await session.scalar(
                            select(func.timezone("utc", func.now()))
                        )

                    stmt = (
                        select(RadiusAdminEvent)
                        .where(RadiusAdminEvent.created_at > last_checked)
                        .order_by(RadiusAdminEvent.created_at.asc())
                    )

                    events = (await session.scalars(stmt)).all()

                    for event in events:
                        logger.info(
                            f"[{event.created_at}] Processing: {event.command.value}"
                        )
                        await execute_radius_command(
                            proc, radmin_lock, event.command, event.payload or {}
                        )
                        last_checked = event.created_at

                    await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Worker encountered an error, backing off: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
