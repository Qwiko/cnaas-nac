from typing import Annotated, Any
from fastapi import status, Response

from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.db import get_async_session
from cnaas_nac.models.oui import DeviceOui
from cnaas_nac.schemas.oui import DeviceOuiResponse, DeviceOuiBase

router = APIRouter(prefix="/oui", tags=["oui"])


@router.get("", response_model=list[DeviceOuiResponse])
async def get_ouis(
    db: Annotated[AsyncSession, Depends(get_async_session)], response: Response
) -> Any:
    """
    Retrieve oui.
    """

    ouis = (await db.execute(select(DeviceOui))).scalars().all()
    
    if not ouis:
        raise NotFound()

    response.headers["X-Total-Count"] = str(len(ouis))

    return ouis


@router.post("", response_model=DeviceOuiResponse, status_code=status.HTTP_201_CREATED)
async def post_oui(
    db: Annotated[AsyncSession, Depends(get_async_session)], input_oui: DeviceOuiBase
) -> Any:
    """
    Post oui.
    """

    oui = DeviceOui(**input_oui.model_dump())

    db.add(oui)
    await db.commit()

    return oui


@router.get("/{oui_name}", response_model=DeviceOuiResponse)
async def get_oui(
    oui_name: str, db: Annotated[AsyncSession, Depends(get_async_session)]
) -> Any:
    """
    Get oui.
    """

    oui = (
        await db.execute(select(DeviceOui).where(DeviceOui.oui == oui_name))
    ).scalar_one_or_none()

    if not oui:
        raise NotFound()

    return oui


@router.put("/{oui_name}", response_model=DeviceOuiResponse)
async def put_oui(
    oui_name: str,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    input_oui: DeviceOuiBase,
) -> Any:
    """
    Put oui.
    """

    oui = (
        await db.execute(select(DeviceOui).where(DeviceOui.oui == oui_name))
    ).scalar_one_or_none()

    if not oui:
        raise NotFound()

    for key, val in input_oui.model_dump(exclude_defaults=True).items():
        setattr(oui, key, val)

    await db.commit()

    return oui


@router.delete("/{oui_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_oui(
    oui_name: str,
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """
    Delete oui.
    """

    oui = (
        await db.execute(select(DeviceOui).where(DeviceOui.oui == oui_name))
    ).scalar_one_or_none()

    if not oui:
        raise NotFound()

    await db.delete(oui)

    await db.commit()

    return None
