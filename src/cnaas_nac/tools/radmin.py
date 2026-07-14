import asyncio

from pydantic import BaseModel, IPvAnyNetwork, ValidationError
from pydantic_extra_types.mac_address import MacAddress
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from cnaas_nac.core.settings import settings
from cnaas_nac.models.radiusadminevent import RadiusAdminEvent, RadiusCommand
from asyncio.subprocess import Process


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
        await proc.stdout.readuntil(b"radmin> ")
    else:
        raise RuntimeError("Failed to read radmin banner")

    return proc


async def send_radmin_command(proc: Process, command: str) -> list[str]:
    if proc.stdin is None or proc.stdout is None:
        raise RuntimeError("Process streams are not available.")

    proc.stdin.write(f"{command}\n".encode("utf-8"))
    await proc.stdin.drain()

    raw_output = await proc.stdout.readuntil(b"radmin> ")

    output_str = raw_output.decode("utf-8")

    # Split to string and remove the first line (the command echo) and the last line (the prompt)
    return output_str.strip().split("\n")[1:-1]


async def radius_clear_client(proc: Process, raw_payload: dict) -> None:
    data = ClearClientPayload(**raw_payload)

    if data.network.num_addresses > 4098:
        print(
            f"Network {data.network} has more than 4098 addresses. Terminating radius service"
        )
        await send_radmin_command(proc, "terminate")
        print("Executed radmin terminate.")
    else:
        sem = asyncio.Semaphore(50)

        async def clear_ip(ip: str) -> None:
            async with sem:
                await send_radmin_command(proc, f"del client ipaddr {ip}")
                print(f"Cleared client {ip}")

        tasks = [clear_ip(str(ip)) for ip in data.network.hosts()]

        await asyncio.gather(*tasks)

    print(f"Cleared network {data.network}")


async def radius_debug_start(proc: Process, raw_payload: dict) -> None:
    data = DebugPayload(**raw_payload)

    # Set the debug level to 3
    await send_radmin_command(
        proc,
        "debug level 3",
    )

    # Get the previous debug conditions
    output_lines = await send_radmin_command(
        proc,
        "show debug condition",
    )
    pre_conditions = None

    # Read the output to check if a condition already exists
    # If it does, we need to add it with an || next to the other conditions
    if output_lines:
        if f'&Calling-Station-Id == "{data.mac}"' in output_lines:
            print(f"Debug condition for {data.mac} already exists.")
            return
        pre_conditions = output_lines[0].strip()
    if pre_conditions:
        debug_condition = f'{pre_conditions} || &Calling-Station-Id == "{data.mac}"'
    else:
        debug_condition = f'&Calling-Station-Id == "{data.mac}"'

    await send_radmin_command(
        proc,
        f"debug condition '{debug_condition}'",
    )
    print(f"Started debug trace for {data.mac}")


async def radius_debug_stop(
    proc: Process,
) -> None:
    # Remove debug conditions
    await send_radmin_command(
        proc,
        "debug condition",
    )

    # Set debug level to 0
    await send_radmin_command(
        proc,
        "debug level 0",
    )

    print("Stopped debug trace")


async def execute_radius_command(
    proc: Process, command: RadiusCommand, raw_payload: dict
) -> None:
    """Executes local sidecar commands asynchronously without blocking the event loop."""
    try:
        if command == RadiusCommand.CLEAR_CLIENT:
            await radius_clear_client(proc, raw_payload)

        elif command == RadiusCommand.DEBUG_START:
            await radius_debug_start(proc, raw_payload)

        elif command == RadiusCommand.DEBUG_STOP:
            await radius_debug_stop(
                proc,
            )

    except ValidationError as e:
        print(f"Payload validation failed for '{command}': {e}")
    except Exception as e:
        print(f"Execution failed for '{command}': {e}")


# Use the asyncpg or psycopg driver for async operations
engine = create_async_engine(f"{settings.POSTGRES_ASYNC_PREFIX}{settings.POSTGRES_URI}")
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def run_worker() -> None:
    print("Starting CNaaS NAC radmin sidecar...")
    last_checked = None

    try:
        print("Setting up radmin session")
        proc = await radmin_setup()

        print("Setting up database session")
        async with AsyncSessionLocal() as session:
            while True:
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
                    print(f"[{event.created_at}] Processing: {event.command.value}")
                    await execute_radius_command(
                        proc, event.command, event.payload or {}
                    )
                    last_checked = event.created_at

                await asyncio.sleep(2)

    except Exception as e:
        print(f"Database error, backing off: {e}")
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
