from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.exceptions import Unauthorized
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.settings import settings
from cnaas_nac.models.nas import NasPort
from cnaas_nac.models.radcheck import RadCheck
from cnaas_nac.models.radreply import RadReply
from cnaas_nac.models.raduserlog import RadUserLog
from cnaas_nac.schemas.internal_auth import InternalAuth

logger = get_logger()


async def add_or_update_userinfo(
    db: AsyncSession, auth: InternalAuth, extra_userinfo_data: dict[str, Any]
):
    return 
    # userinfo = (
    #     await db.execute(
    #         select(RadUserInfo).where(RadUserInfo.username == auth.username)
    #     )
    # ).scalar_one_or_none()

    # if not userinfo:
    #     # Create new userinfo if not found
    #     userinfo = RadUserInfo(
    #         username=auth.username,
    #         authdate=datetime.now(),
    #         access_start=None,
    #         access_stop=None,
    #         accepts=0,
    #         rejects=0,
    #     )
    #     db.add(userinfo)

    # for key, val in extra_userinfo_data.items():
    #     if key == "accepts":
    #         userinfo.accepts += 1
    #     elif key == "rejects":
    #         userinfo.rejects += 1
    #     else:
    #         setattr(userinfo, key, val)

    await db.commit()


async def accept(db: AsyncSession, auth: InternalAuth, comment: str = None) -> dict:
    """Helper function to return a Access-Accept"""
    replies_ret = await db.execute(
        select(RadReply).where(RadReply.username == auth.username)
    )
    replies = replies_ret.scalars().all()

    # for reply in replies:
    #     logger.debug("reply:", reply)

    reply = {
        reply.attribute: {"op": reply.op, "value": reply.value} for reply in replies
    }

    await add_or_update_userinfo(db, auth, {"accepts": True, "reason": "accept"})

    return reply


async def reject(db: AsyncSession, auth: InternalAuth, error_message: str, comment: str = None) -> None:
    """
    Reject the user with a 401.

    From FreeRADIUS documentation:

    #  Authorize/Authenticate
    #
    #  Code   Meaning       Process body  Module code
    #  404    not found     no            notfound
    #  410    gone          no            notfound
    #  403    forbidden     no            userlock
    #  401    unauthorized  yes           reject
    #  204    no content    no            ok
    #  2xx    successful    yes           ok/updated
    #  5xx    server error  no            fail
    #  xxx    -             no            invalid
    #
    #  The status code is held in %{reply:REST-HTTP-Status-Code}.
    """
    await add_or_update_userinfo(db, auth, {"rejects": True, "reason": "reject"})

    raise Unauthorized(error_message)


async def create_new_user(db: AsyncSession, auth: InternalAuth) -> None:
    vlan = settings.RADIUS_DEFAULT_VLAN
    try:
        user = RadCheck(
            username=auth.username,
            attribute="Cleartext-Password",
            value=auth.password,
            op="",
        )
        tunnel_id = RadReply(
            username=auth.username,
            attribute="Tunnel-Private-Group-Id",
            op=":=",
            value=str(vlan),
        )
        tunnel_type = RadReply(
            username=auth.username, attribute="Tunnel-Type", op=":=", value="VLAN"
        )
        tunnel_medium = RadReply(
            username=auth.username,
            attribute="Tunnel-Medium-Type",
            op=":=",
            value="IEEE-802",
        )
        nas_port = NasPort(
            username=auth.username,
            nas_ip_address=auth.nas_ip_address,
            nas_identifier=auth.nas_identifier,
            nas_port_id=auth.nas_port_id,
            calling_station_id=auth.calling_station_id,
            called_station_id=auth.called_station_id,
        )
        # userinfo = RadUserInfo(
        #     username=auth.username,
        #     reason="",
        #     comment="comment",
        #     authdate=datetime.utcnow(),
        #     access_start=None,
        #     access_stop=None,
        #     accepts=0,
        #     rejects=0,
        # )

        db.add(user)
        db.add(tunnel_id)
        db.add(tunnel_type)
        db.add(tunnel_medium)
        db.add(nas_port)
        # db.add(userinfo)
        await db.commit()
    except Exception as e:
        error_msg = str(e)
        logger.error(error_msg)
        raise Unauthorized(error_msg)
