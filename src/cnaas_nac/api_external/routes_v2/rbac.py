from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.models.rbac import Group, GroupPermission


class GroupPermissionModel(BaseModel):
    path: str
    methods: list[Literal["GET", "POST", "PUT", "DELETE"]]


# Base properties shared across multiple schemas
class GroupBase(BaseModel):
    name: str
    allowed_vlans: list[str | int]
    permissions: list[GroupPermissionModel]


class GroupCreate(GroupBase):
    pass


# Schema for Responses (Returns the ID from the database)
class GroupResponse(GroupBase):
    id: int


router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    request: Request,
    group_in: GroupCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Create a new group."""
    stmt = select(Group).where(Group.name == group_in.name)
    existing_group = (await db.execute(stmt)).scalar_one_or_none()

    if existing_group:
        raise HTTPException(status_code=400, detail="Group name already registered")

    db_group = Group(name=group_in.name, allowed_vlans=group_in.allowed_vlans)

    # Create the subpermissions using the ALIASED database model
    db_group.permissions = [
        GroupPermission(**perm.model_dump()) for perm in group_in.permissions
    ]
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)

    return db_group


@router.get("/", response_model=list[GroupResponse])
async def read_groups(db: Annotated[AsyncSession, Depends(get_async_session)]):
    """Retrieve all groups with pagination."""
    groups = (await db.execute(select(Group))).scalars().all()
    return groups


@router.get("/{group_id}", response_model=GroupResponse)
async def read_group(
    group_id: int, db: Annotated[AsyncSession, Depends(get_async_session)]
):
    """Get a specific group by ID."""
    db_group = (
        await db.execute(select(Group).where(Group.id == group_id))
    ).scalar_one_or_none()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_in: GroupCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
):
    """Update a group's details."""
    db_group = (
        await db.execute(select(Group).where(Group.id == group_id))
    ).scalar_one_or_none()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Extract only the fields the user actually provided in the request
    update_data = group_in.model_dump(exclude_unset=True)

    # Apply updates to the database model
    for key, value in update_data.items():
        setattr(db_group, key, value)

    await db.commit()
    await db.refresh(db_group)
    return db_group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int, db: Annotated[AsyncSession, Depends(get_async_session)]
):
    """Delete a group."""
    db_group = (
        await db.execute(select(Group).where(Group.id == group_id))
    ).scalar_one_or_none()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")

    await db.delete(db_group)
    await db.commit()
    return None  # 204 No Content doesn't need a response body
