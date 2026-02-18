from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import and_, inspect, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.api_internal.schemas import AccessAccept, InternalAuth
from cnaas_nac.api_internal.utils import accept, create_new_user, reject
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.settings import settings
from cnaas_nac.models.nas import NasPort
from cnaas_nac.models.radcheck import RadCheck

logger = get_logger()

router = APIRouter(prefix="/api/v2", tags=["auth"])


@router.post("/auth", response_model=AccessAccept)
async def post_auth(
    db: Annotated[AsyncSession, Depends(get_async_session)], auth: InternalAuth
) -> Any:
    """
    Internal endpoint that is used from the Freeradius rest module
    """

    user = (
        await db.execute(select(RadCheck).where(RadCheck.username == auth.username))
    ).scalar_one_or_none()

    # User is not found, creating -> Reject
    if not user:
        if settings.RADIUS_SLAVE:
            logger.info("Configured as RADIUS_SLAVE, skipping user creation.")
            await reject(db, auth, "user not found")
        else:
            logger.info(f"User: {auth.username} not found, creating.")
            user = await create_new_user(db, auth)

    assert user

    user_vlan = user.vlan if user.vlan else settings.RADIUS_DEFAULT_VLAN

    # Make sure user_vlan is actually an int.
    assert isinstance(user_vlan, int)

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
        logger.debug(f"User: {auth.username}, connected on a known previous port.")

        # Update nasport if some information have changed.
        # For example changed hostname but same called_station_id
        # Or replaced switch, same hostname but changed called_station_id.
        for k, v in auth_nas_port_dict.items():
            if getattr(db_nas_port, k) != v:
                setattr(db_nas_port, k, v)

        if inspect(db_nas_port).modified:
            logger.debug(
                f"Port: {db_nas_port.nas_identifier}:{db_nas_port.nas_port_id} have been modified with new data."
            )
        else:
            # Force updated_at update for this nasport.
            # Even if the data is the same.
            logger.debug(
                f"No new data for port: {db_nas_port.nas_identifier}:{db_nas_port.nas_port_id}, still updating updated_at to use as last_seen."
            )
            db_nas_port.updated_at = datetime.now(timezone.utc)

        await db.commit()

    if not db_nas_port and user_vlan not in settings.RADIUS_LOCK_VLANS:
        logger.info(f"User: {auth.username} connected on new port. Adding nasport")
        db_nas_port = NasPort(**auth_nas_port_dict)
        db.add(db_nas_port)
        await db.commit()

    now = datetime.now(timezone.utc)

    if user.access_start and now < user.access_start:
        logger.info(f"User: {auth.username} rejected. Time is before access_start.")
        await reject(db, auth, "time is before access_start")

    if user.access_stop and now > user.access_stop:
        logger.info(f"User: {auth.username} rejected. Time is after access_stop.")
        await reject(db, auth, "time is after access_stop")

    if user_vlan in settings.RADIUS_LOCK_VLANS:
        # Get expected port this user should be connected to.
        expected_port = (
            (
                await db.execute(
                    select(NasPort)
                    .where(
                        NasPort.username == auth.username,
                    )
                    .order_by(NasPort.updated_at.desc())
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
            logger.info(error_msg)

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
        await reject(db, auth, "user disabled")

    # Normal non-locked user
    if user.enabled:
        logger.info(f"User: {auth.username} is enabled, accepting.")
        return await accept(db, auth)

    logger.info(f"User: {auth.username} is found but not enabled, rejecting.")
    await reject(db, auth, "user disabled")
