from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.security import User, get_current_user
from cnaas_nac.models.rbac import RBAC, RBACPermission


class RBACPermissionModel(BaseModel):
    path: str
    methods: list[Literal["GET", "POST", "PUT", "DELETE"]]


# Base properties shared across multiple schemas
class RBACBase(BaseModel):
    name: str
    allowed_group_ids: list[int]
    permissions: list[RBACPermissionModel]


class RBACCreateUpdate(RBACBase):
    pass


# Schema for Responses (Returns the ID from the database)
class RBACResponse(RBACBase):
    id: int


router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.post("", response_model=RBACResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    request: Request,
    group_in: RBACCreateUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new group."""
    stmt = select(RBAC).where(RBAC.name == group_in.name)
    existing_group = (await db.execute(stmt)).scalar_one_or_none()

    if existing_group:
        raise HTTPException(status_code=400, detail="Group name already registered")

    db_group = RBAC(name=group_in.name, allowed_group_ids=group_in.allowed_group_ids)

    # Create the subpermissions using the ALIASED database model
    db_group.permissions = [
        RBACPermission(**perm.model_dump()) for perm in group_in.permissions
    ]
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)

    return db_group


@router.get("", response_model=list[RBACResponse])
async def read_rbac(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Retrieve all RBAC entries with pagination."""
    rbac_entries = (await db.execute(select(RBAC))).scalars().all()
    return rbac_entries


@router.get("/{id}", response_model=RBACResponse)
async def read_rbac_entry(
    rbac_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a specific RBAC entry by ID."""
    db_group = (
        await db.execute(select(RBAC).where(RBAC.id == rbac_id))
    ).scalar_one_or_none()
    if not db_group:
        raise HTTPException(status_code=404, detail="RBAC not found")
    return db_group


@router.put("/{id}", response_model=RBACResponse)
async def update_rbac(
    rbac_id: Annotated[int, Path(alias="id")],
    group_in: RBACCreateUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a group's details."""
    db_group = (
        await db.execute(select(RBAC).where(RBAC.id == rbac_id))
    ).scalar_one_or_none()
    if not db_group:
        raise HTTPException(status_code=404, detail="RBAC not found")

    # Extract only the fields the user actually provided in the request
    update_data = group_in.model_dump(exclude_unset=True)

    # Apply updates to the database model
    for key, value in update_data.items():
        setattr(db_group, key, value)

    await db.commit()
    await db.refresh(db_group)
    return db_group


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rbac(
    rbac_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a rbac group."""
    db_group = (
        await db.execute(select(RBAC).where(RBAC.id == rbac_id))
    ).scalar_one_or_none()
    if not db_group:
        raise HTTPException(status_code=404, detail="RBAC not found")

    await db.delete(db_group)
    await db.commit()
    return None  # 204 No Content doesn't need a response body
