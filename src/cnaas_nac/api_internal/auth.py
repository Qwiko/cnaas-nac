from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import Integer, and_, cast, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_dirty

from cnaas_nac.api_internal.utils import accept, create_new_user, reject
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.settings import settings
from cnaas_nac.models.nas import NasPort
from cnaas_nac.models.radcheck import RadCheck
from cnaas_nac.models.radreply import RadReply
from cnaas_nac.schemas.internal_auth import AccessAccept, InternalAuth

logger = get_logger()

router = APIRouter(prefix="/api/v2", tags=["auth"])


@router.post("/auth", response_model=AccessAccept)
async def post_auth(
    db: Annotated[AsyncSession, Depends(get_async_session)], auth: InternalAuth
) -> dict:
    """
    Internal endpoint that is used from the Freeradius rest module
    """
    user = (
        await db.execute(select(RadCheck).where(RadCheck.username == auth.username))
    ).scalar_one_or_none()

    user_vlan = (
        (
            await db.execute(
                select(cast(RadReply.value, Integer)).where(
                    RadReply.username == auth.username,
                    RadReply.attribute == "Tunnel-Private-Group-Id",
                )
            )
        )
        .scalars()
        .first()
    )

    if not user_vlan:
        user_vlan = settings.RADIUS_DEFAULT_VLAN

    # User is not found, creating -> Reject
    if not user:
        if settings.RADIUS_SLAVE:
            logger.debug("Configured as RADIUS_SLAVE, skipping user creation.")
        else:
            logger.debug(f"User: {auth.username} not found, creating.")
            await create_new_user(db, auth)

        await reject(db, auth, "user not found")

    # Dictionary with key:value needed to create a NasPort
    # from auth model.
    auth_nas_port_dict = {
        k: v for k, v in auth.model_dump().items() if hasattr(NasPort, k)
    }

    db_nas_port = (
        await db.execute(
            select(NasPort).where(
                NasPort.username == auth.username,
                or_(
                    and_(
                        NasPort.called_station_id == auth.called_station_id,
                        NasPort.nas_port_id == auth.nas_port_id,
                    ),
                    and_(
                        NasPort.nas_identifier == auth.nas_identifier,
                        NasPort.nas_port_id == auth.nas_port_id,
                    ),
                ),
            )
        )
    ).scalar_one_or_none()

    if db_nas_port:
        logger.debug(
            f"User: {auth.username}, connected on a previous port, updating nasport."
        )
        logger.debug(str(auth.model_dump()))

        # Force last_seen update for this nasport.
        # Even if the data is the same.
        flag_dirty(db_nas_port)

        # Update nasport if some information have changed.
        # For example changed hostname but same called_station_id
        # Or replaced switch, same hostname but changed called_station_id.
        for k, v in auth_nas_port_dict.items():
            if getattr(db_nas_port, k) != v:
                setattr(db_nas_port, k, v)

        await db.commit()

    if not db_nas_port and user_vlan not in settings.RADIUS_LOCK_VLANS:
        logger.info(f"User: {auth.username} connected on new port. Adding nasport")
        db_nas_port = NasPort(**auth_nas_port_dict)
        db.add(db_nas_port)
        await db.commit()

    # TODO: Add check for time-based access/reject here

    if user_vlan in settings.RADIUS_LOCK_VLANS:
        # Get expected port this user should be connected to.
        expected_port = (
            (
                await db.execute(
                    select(NasPort)
                    .where(
                        NasPort.username == auth.username,
                    )
                    .order_by(NasPort.last_seen.desc())
                )
            )
            .scalars()
            .first()
        )
        if not expected_port:
            logger.info(
                f"User: {auth.username} does not have any expected port, creating one."
            )
            expected_port = NasPort(**auth_nas_port_dict)
            db.add(expected_port)
            await db.commit()

        if not db_nas_port or (user.enabled and expected_port.id != db_nas_port.id):
            logger.info(
                f"User: {auth.username} did not connect on expected locked port, rejecting."
            )
            error_msg = f"User: {auth.username} is connecting on: {auth.nas_identifier}:{auth.nas_port_id}, expected: {expected_port.nas_identifier}:{expected_port.nas_port_id}"
            logger.debug(error_msg)

            await reject(db, auth, "not expected port")

        if db_nas_port and user.enabled and expected_port.id == db_nas_port.id:
            logger.info(
                f"User: {auth.username} connected on expected locked port, accepting."
            )
            return await accept(db, auth)

        logger.info(
            f"User: {auth.username} is disabled on a locked vlan with changing expected port."
        )
        if db_nas_port:
            await db.delete(db_nas_port)
        await db.commit()
        await reject(db, auth)

    # Normal non-locked user
    if user.enabled:
        logger.debug(f"User: {auth.username} is enabled, accepting.")
        return await accept(db, auth)

    logger.debug(f"User: {auth.username} is found but not enabled, rejecting.")
    await reject(db, auth, "User not found.")
