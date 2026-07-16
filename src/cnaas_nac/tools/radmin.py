import asyncio
import os
from asyncio.subprocess import Process

from netutils.mac import is_valid_mac
from pydantic import BaseModel, IPvAnyNetwork, ValidationError
from pydantic_extra_types.mac_address import MacAddress
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.settings import settings
from cnaas_nac.models.radiusadminevent import (
    RadiusAdminEvent,
    RadiusCommand,
    RadiusDebugLog,
)
from cnaas_nac.schemas.debug import DebugBase

logger = get_logger()

LOG_DIR = "/var/log/radius"
LOG_NAME = "radmin_debug.log"
TRACE_FILE = f"{LOG_DIR}/{LOG_NAME}"
NODE_NAME = os.environ.get("HOSTNAME", "unknown")

FREERADIUS_MAP = {
    "username": "User-Name",
    "nas_identifier": "NAS-Identifier",
    "nas_port_id": "NAS-Port-Id",
    "nas_port_type": "NAS-Port-Type",
    "calling_station_id": "Calling-Station-Id",
    "called_station_id": "Called-Station-Id",
    "nas_ip_address": "NAS-IP-Address",
    "realm": "Realm",
}


class ClearClientPayload(BaseModel):
    network: IPvAnyNetwork


def generate_mac_formats(mac: MacAddress) -> list[str]:
    """
    Takes a MAC address and returns a list of all common NAS formats
    (colon, dash, dot, and bare in both upper and lower case).
    """
    # Normalize
    raw_mac = str(mac).replace(":", "").replace("-", "").replace(".", "").lower()

    # XX:XX:XX:XX:XX:XX
    colon_lower = ":".join(raw_mac[i : i + 2] for i in range(0, 12, 2))
    colon_upper = colon_lower.upper()

    # XX-XX-XX-XX-XX-XX
    dash_lower = colon_lower.replace(":", "-")
    dash_upper = colon_upper.replace(":", "-")

    # XXXX.XXXX.XXXX
    dot_lower = ".".join(raw_mac[i : i + 4] for i in range(0, 12, 4))
    dot_upper = dot_lower.upper()

    return [
        colon_lower,
        colon_upper,
        dash_lower,
        dash_upper,
        dot_lower,
        dot_upper,
        raw_mac,
        raw_mac.upper(),
    ]


async def continuous_log_streamer() -> None:
    """Runs forever, tailing the file and inserting to DB if a debug is active."""
    logger.info("Starting continuous log streamer...")
    counter = 0

    while True:
        try:
            await (await asyncio.create_subprocess_exec("touch", TRACE_FILE)).wait()

            proc = await asyncio.create_subprocess_exec(
                "tail", "-n", "0", "-F", TRACE_FILE, stdout=asyncio.subprocess.PIPE
            )

            assert proc.stdout is not None, (
                "Failed to capture stdout from tail process."
            )

            async with AsyncSessionLocal() as session:
                async for line in proc.stdout:
                    decoded_line = line.decode("utf-8").strip()
                    if decoded_line:
                        log = RadiusDebugLog(node_name=NODE_NAME, log_line=decoded_line)
                        session.add(log)
                        await session.commit()

                        counter += 1

                        # Prune occasionally old logs
                        if counter >= 100:
                            counter = 0
                            logger.debug("Deleting old logs for this node")
                            result = await session.execute(
                                select(RadiusDebugLog.id)
                                .order_by(RadiusDebugLog.created_at.desc())
                                .offset(1000)
                            )

                            old_ids = result.scalars().all()

                            if old_ids:
                                await session.execute(
                                    delete(RadiusDebugLog).where(
                                        RadiusDebugLog.node_name == NODE_NAME,
                                        RadiusDebugLog.id.in_(old_ids),
                                    )
                                )
                                await session.commit()

        except Exception as e:
            logger.info(f"Log streamer encountered an error: {e}")
            # Back off and restart the tail process if something breaks
            await asyncio.sleep(5)


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
        logger.debug(f"RAW: {output_str}")
        lines = [
            line
            for line in output_str.strip().split("\n")
            if line != "radmin>" and line != command
        ]

        # Clean last line if it is concatinated with 'radmin> '
        if len(lines) > 1 and lines[-1].endswith("radmin>"):
            lines[-1] = lines[-1][:-7]

        logger.debug(f"lines: {len(lines)} - {lines}")

        return lines


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
    proc: Process, lock: asyncio.Lock, session: AsyncSession, raw_payload: dict
) -> None:
    data = DebugBase(**raw_payload)

    # Create the debug condition string
    condition_parts = []

    for field in data.model_fields_set:
        value = getattr(data, field)
        if is_valid_mac(value):
            mac_formats = generate_mac_formats(value)
            mac_conditions = [f'&{FREERADIUS_MAP[field]} == "{m}"' for m in mac_formats]
            condition_parts.append("(" + " || ".join(mac_conditions) + ")")
        else:
            condition_parts.append(f'&{FREERADIUS_MAP[field]} == "{value}"')

    condition_string = " && ".join(condition_parts)

    # Reset radius debug condition so no residual logs come through
    await send_radmin_command(proc, lock, "debug condition")

    # Resets logs related to this NODE_NAME
    # Issuing a CLEAR logs from the API resets all logs
    await session.execute(
        delete(RadiusDebugLog).where(RadiusDebugLog.node_name == NODE_NAME)
    )
    await session.commit()

    # Reset debug file
    await (
        await asyncio.create_subprocess_exec(
            "sh",
            "-c",
            f"echo 'Starting debugging' > {TRACE_FILE}",
        )
    ).wait()

    await send_radmin_command(proc, lock, f"debug file {LOG_NAME}")
    await send_radmin_command(proc, lock, f"debug condition '{condition_string}'")
    logger.info(
        f"Started debugging, conditions: {data.model_dump(exclude_unset=True, exclude_none=True)}"
    )


async def radius_debug_stop(proc: Process, lock: asyncio.Lock) -> None:
    await send_radmin_command(proc, lock, "debug condition")
    await send_radmin_command(proc, lock, "debug file")
    await send_radmin_command(proc, lock, "debug level 0")
    await (
        await asyncio.create_subprocess_exec(
            "sh",
            "-c",
            f"echo 'Stopped debugging' >> {TRACE_FILE}",
        )
    ).wait()

    logger.info("Stopped debug trace")


async def radius_debug_clear(proc: Process, lock: asyncio.Lock) -> None:
    # Reset debug file
    await (
        await asyncio.create_subprocess_exec(
            "sh", "-c", f"echo 'Cleared debug logs' > {TRACE_FILE}"
        )
    ).wait()

    # Resetting the DB is done in the external api.
    logger.info("Cleared debug logs")


async def execute_radius_command(
    proc: Process,
    lock: asyncio.Lock,
    session: AsyncSession,
    command: RadiusCommand,
    raw_payload: dict,
) -> None:
    try:
        if command == RadiusCommand.CLEAR_CLIENT:
            await radius_clear_client(proc, lock, raw_payload)

        elif command == RadiusCommand.DEBUG_START:
            await radius_debug_start(proc, lock, session, raw_payload)

        elif command == RadiusCommand.DEBUG_STOP:
            await radius_debug_stop(proc, lock)

        elif command == RadiusCommand.DEBUG_CLEAR:
            await radius_debug_clear(proc, lock)

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
                            proc,
                            radmin_lock,
                            session,
                            event.command,
                            event.payload or {},
                        )
                        last_checked = event.created_at

                    # Ensure debugging is active
                    # When freeradius restarts debugging stops
                    stmt = (
                        select(RadiusAdminEvent)
                        .where(
                            RadiusAdminEvent.command.in_(
                                [RadiusCommand.DEBUG_STOP, RadiusCommand.DEBUG_START]
                            )
                        )
                        .distinct()
                        .order_by(RadiusAdminEvent.created_at.desc())
                    )

                    event_mismatch = (await session.scalars(stmt)).first()
                    logger.debug("Checking for debug state mismatch")
                    if (
                        event_mismatch
                        and event_mismatch.command == RadiusCommand.DEBUG_START
                    ):
                        # Debugging should be active
                        lines = await send_radmin_command(
                            proc, radmin_lock, "show debug condition"
                        )
                        logger.debug(f"LINES FROM SEND_CMD: {lines}")
                        if not lines or len(lines) == 1 and lines[0] == "":
                            logger.info(
                                "Debug logging should be active, activating again"
                            )
                            await radius_debug_start(
                                proc, radmin_lock, session, event_mismatch.payload
                            )
                    elif (
                        event_mismatch
                        and event_mismatch.command == RadiusCommand.DEBUG_STOP
                    ):
                        # Debugging should not be active
                        lines = await send_radmin_command(
                            proc, radmin_lock, "show debug condition"
                        )
                        logger.debug(f"LINES FROM SEND_CMD: {lines}")
                        if len(lines) >= 1 and lines[0] != "":
                            logger.info(
                                "Debug logging should not be active, disabling debug"
                            )
                            await radius_debug_stop(proc, radmin_lock)

                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Worker encountered an error, backing off: {e}")
            await asyncio.sleep(5)


async def main() -> None:
    await asyncio.gather(run_worker(), continuous_log_streamer())


if __name__ == "__main__":
    asyncio.run(main())
