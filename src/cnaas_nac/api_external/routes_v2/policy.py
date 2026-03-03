from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi_filter import FilterDepends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.exceptions import NotFound
from cnaas_nac.core.logging import get_logger
from cnaas_nac.core.pagination import PaginationParams
from cnaas_nac.core.security import get_current_user
from cnaas_nac.filters.policy import PolicyFilter
from cnaas_nac.models.policy import Policy, PolicyCondition, PolicyReply
from cnaas_nac.schemas.policy import (
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
)

logger = get_logger()

router = APIRouter(prefix="/policy", tags=["policy"])


@router.get("", response_model=list[PolicyResponse])
async def read_policies(
    policy_filter: Annotated[PolicyFilter, FilterDepends(PolicyFilter)],
    pagination_params: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> Any:
    """
    Get policies.
    """

    query = select(Policy)
    query = policy_filter.filter(query)
    query = policy_filter.sort(query)
    query = query.offset(pagination_params.offset).limit(pagination_params.size)

    count_query = select(func.count()).select_from(Policy)
    count_query = policy_filter.filter(count_query)

    total_count = (await db.execute(count_query)).scalar_one()

    response.headers["X-Total-Count"] = str(total_count)

    if total_count == 0:
        response.status_code = status.HTTP_404_NOT_FOUND

    return (await db.execute(query)).scalars().all()


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def post_policy(
    input_policy: PolicyCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Post new policy.
    """

    existing_rule = (
        await db.execute(select(Policy).where(Policy.name == input_policy.name))
    ).scalar_one_or_none()
    if existing_rule:
        raise RequestValidationError(
            [
                {
                    "loc": ["body", "name"],
                    "msg": "A Policy with that name already exists.",
                }
            ]
        )

    policy = Policy(
        **{
            k: v
            for k, v in input_policy.model_dump().items()
            if hasattr(Policy, k) and k != "conditions" and k != "replies"
        }
    )

    policy.conditions = [
        PolicyCondition(**{k: v for k, v in cond.model_dump().items()})
        for cond in input_policy.conditions
    ]

    policy.replies = [
        PolicyReply(**{k: v for k, v in cond.model_dump().items()})
        for cond in input_policy.replies
    ]

    db.add(policy)

    await db.commit()
    await db.refresh(policy)
    return policy


@router.get("/{policy_id}", response_model=PolicyResponse)
async def read_policy(
    policy_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Retrieve individual policy.
    """

    policy = (
        await db.execute(select(Policy).where(Policy.id == policy_id))
    ).scalar_one_or_none()

    if not policy:
        raise NotFound()

    return policy


@router.put("/{policy_id}", response_model=PolicyResponse)
async def put_policy(
    policy_id: int,
    input_policy: PolicyUpdate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> Any:
    """
    Update policy.
    """

    existing_policy = (
        await db.execute(select(Policy).where(Policy.id == policy_id))
    ).scalar_one_or_none()

    if not existing_policy:
        raise NotFound()

    for k, v in input_policy.model_dump().items():
        if getattr(existing_policy, k) != v and k != "conditions" and k != "replies":
            setattr(existing_policy, k, v)

    # Recreate
    existing_policy.conditions = [
        PolicyCondition(**{k: v for k, v in cond.model_dump().items()})
        for cond in input_policy.conditions
    ]

    existing_policy.replies = [
        PolicyReply(**{k: v for k, v in cond.model_dump().items()})
        for cond in input_policy.replies
    ]

    await db.commit()
    await db.refresh(existing_policy)

    return existing_policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """
    Delete policy.
    """

    policy = (
        await db.execute(select(Policy).where(Policy.id == policy_id))
    ).scalar_one_or_none()

    if not policy:
        raise NotFound()

    await db.delete(policy)

    await db.commit()

    return None
