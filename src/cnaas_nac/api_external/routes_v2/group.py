# from typing import Annotated, Any
# from fastapi import status, Response

# from fastapi import APIRouter, Depends
# from sqlalchemy import select, delete
# from sqlalchemy.ext.asyncio import AsyncSession

# from cnaas_nac.core.exceptions import NotFound
# from cnaas_nac.core.db import get_async_session
# from cnaas_nac.models.radgroupcheck import RadGroupCheck
# from cnaas_nac.schemas.groups import GroupBase, GroupResponse

# router = APIRouter(prefix="/groups", tags=["groups"])


# @router.get("", response_model=list[GroupResponse])
# async def get_groups(
#     db: Annotated[AsyncSession, Depends(get_async_session)], response: Response
# ) -> Any:
#     """
#     Retrieve group.
#     """

#     groups = (await db.execute(select(Group))).scalars().all()

#     if not groups:
#         raise NotFound()

#     response.headers["X-Total-Count"] = str(len(groups))

#     return groups


# @router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
# async def post_group(
#     db: Annotated[AsyncSession, Depends(get_async_session)], input_group: GroupBase
# ) -> Any:
#     """
#     Post group.
#     """

#     group = Group(**input_group.model_dump())

#     db.add(group)
#     await db.commit()

#     return group


# @router.get("/{group_name}", response_model=GroupResponse)
# async def get_group(
#     group_name: str, db: Annotated[AsyncSession, Depends(get_async_session)]
# ) -> Any:
#     """
#     Get group.
#     """

#     oui = (
#         await db.execute(select(Group).where(Group.name == group_name))
#     ).scalar_one_or_none()

#     if not oui:
#         raise NotFound()

#     return oui


# @router.put("/{group_name}", response_model=GroupResponse)
# async def put_group(
#     group_name: str,
#     db: Annotated[AsyncSession, Depends(get_async_session)],
#     input_group: GroupBase,
# ) -> Any:
#     """
#     Put group.
#     """

#     group = (
#         await db.execute(select(Group).where(Group.name == group_name))
#     ).scalar_one_or_none()

#     if not group:
#         raise NotFound()

#     for key, val in input_group.model_dump(exclude_defaults=True).items():
#         setattr(group, key, val)

#     await db.commit()

#     return group


# @router.delete("/{group_name}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_group(
#     group_name: str,
#     db: Annotated[AsyncSession, Depends(get_async_session)],
# ) -> None:
#     """
#     Delete group.
#     """

#     group = (
#         await db.execute(select(Group).where(Group.name == group_name))
#     ).scalar_one_or_none()

#     if not group:
#         raise NotFound()

#     await db.delete(group)

#     await db.commit()

#     return None
