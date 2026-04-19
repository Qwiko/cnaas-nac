from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.security import User, get_current_user
from cnaas_nac.models.endpoint import EndpointGroup
from cnaas_nac.models.rbac import RBAC, RBACPermission
from cnaas_nac.schemas.rbac import RBACCreate, RBACResponse, RBACUpdate

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.post("", response_model=RBACResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    request: Request,
    rbac_in: RBACCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RBAC:
    """Create a new rbac."""
    stmt = select(RBAC).where(RBAC.name == rbac_in.name)
    existing_rbac = (await db.execute(stmt)).scalar_one_or_none()

    if existing_rbac:
        raise HTTPException(status_code=400, detail="RBAC name already registered")

    stmt = select(EndpointGroup).where(
        EndpointGroup.id.in_(rbac_in.allowed_endpoint_groups)
    )
    endpoint_groups = (await db.execute(stmt)).scalars().all()

    db_rbac = RBAC(name=rbac_in.name, allowed_endpoint_groups=endpoint_groups)

    # Create the permissions
    db_rbac.permissions = [
        RBACPermission(**perm.model_dump()) for perm in rbac_in.permissions
    ]
    db.add(db_rbac)
    await db.commit()
    await db.refresh(db_rbac)

    return db_rbac


@router.get("", response_model=list[RBACResponse])
async def read_rbac(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Sequence[RBAC]:
    """Retrieve all RBAC entries with pagination."""
    rbac_entries = (await db.execute(select(RBAC))).scalars().all()
    return rbac_entries


@router.get("/{id}", response_model=RBACResponse)
async def read_rbac_entry(
    rbac_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RBAC:
    """Get a specific RBAC entry by ID."""
    db_rbac = (
        await db.execute(select(RBAC).where(RBAC.id == rbac_id))
    ).scalar_one_or_none()
    if not db_rbac:
        raise HTTPException(status_code=404, detail="RBAC not found")
    return db_rbac


@router.put("/{id}", response_model=RBACResponse)
async def update_rbac(
    rbac_id: Annotated[int, Path(alias="id")],
    group_in: RBACUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RBAC:
    """Update a group's details."""
    db_rbac = (
        await db.execute(select(RBAC).where(RBAC.id == rbac_id))
    ).scalar_one_or_none()
    if not db_rbac:
        raise HTTPException(status_code=404, detail="RBAC not found")

    # Extract only the fields the user actually provided in the request
    update_data = group_in.model_dump(exclude_unset=True)

    # Apply updates to the database model
    for key, value in update_data.items():
        if key == "allowed_endpoint_groups":
            stmt = select(EndpointGroup).where(EndpointGroup.id.in_(value))
            endpoint_groups = (await db.execute(stmt)).scalars().all()
            setattr(db_rbac, "allowed_endpoint_groups", endpoint_groups)
        elif key == "permissions":
            # Clear existing permissions and add new ones
            db_rbac.permissions.clear()
            db_rbac.permissions = [RBACPermission(**perm) for perm in value]
        else:
            setattr(db_rbac, key, value)

    await db.commit()
    await db.refresh(db_rbac)
    return db_rbac


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rbac(
    rbac_id: Annotated[int, Path(alias="id")],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete a rbac group."""
    db_group = (
        await db.execute(select(RBAC).where(RBAC.id == rbac_id))
    ).scalar_one_or_none()
    if not db_group:
        raise HTTPException(status_code=404, detail="RBAC not found")

    await db.delete(db_group)
    await db.commit()
    return None  # 204 No Content doesn't need a response body
