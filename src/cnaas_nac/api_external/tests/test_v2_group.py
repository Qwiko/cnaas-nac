# import pytest
# from fastapi import status
# from httpx import AsyncClient
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# from cnaas_nac.models.radgroupcheck import Group


# pytestmark = pytest.mark.anyio


# async def test_v1_group_post(ext_client: AsyncClient) -> None:
#     response = await ext_client.post(
#         "/api/v1.0/groups",
#         json={"name": "group_1", "fieldname": "vlan", "condition": "vlan_1"},
#     )
#     assert response.status_code == status.HTTP_201_CREATED
#     assert isinstance(response.json().get("id"), int)
#     assert response.json().get("name") == "group_1"


# async def test_v1_group_post_fail(ext_client: AsyncClient) -> None:
#     # No data 
#     response = await ext_client.post(
#         "/api/v1.0/groups",
#         json={},
#     )
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

#     # No fieldname, condition
#     response = await ext_client.post(
#         "/api/v1.0/groups",
#         json={"name": "name"},
#     )
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# async def test_v1_group_get(db: AsyncSession, ext_client: AsyncClient) -> None:
#     # Create entry in db
#     db.add(Group(name="group1", fieldname="vlan", condition="vlan_1"))
#     await db.commit()

#     response = await ext_client.get(
#         "/api/v1.0/groups",
#     )

#     res_json = response.json()
#     assert response.status_code == status.HTTP_200_OK
#     assert isinstance(res_json, list)
#     assert len(res_json) >= 1
#     assert "group1" in [a.get("name") for a in res_json]
#     assert int(response.headers.get("X-Total-Count")) >= 1


# async def test_v1_group_notfound(ext_client: AsyncClient) -> None:
#     response = await ext_client.get(
#         "/api/v1.0/groups",
#     )

#     assert response.status_code == status.HTTP_404_NOT_FOUND


# async def test_v1_group_get_name(db: AsyncSession, ext_client: AsyncClient) -> None:
#     # Create entry in db
#     db.add(Group(name="group1", fieldname="vlan", condition="vlan_1"))
#     await db.commit()
#     response = await ext_client.get(
#         "/api/v1.0/groups/group1",
#     )

#     res_json = response.json()
#     assert response.status_code == status.HTTP_200_OK
#     assert isinstance(res_json, dict)
#     assert "group1" == res_json.get("name")


# async def test_v1_group_name_notfound(ext_client: AsyncClient) -> None:
#     for method in ["GET", "PUT", "DELETE"]:
#         response = await ext_client.request(
#             method,
#             "/api/v1.0/groups/some_not_found_name",
#             json={"name": "group_11", "fieldname": "vlan", "condition": "vlan_11"},
#         )

#         assert response.status_code == status.HTTP_404_NOT_FOUND


# async def test_v1_group_put_name(db: AsyncSession, ext_client: AsyncClient) -> None:
#     # Create entry in db
#     db.add(Group(name="group0", fieldname="vlan", condition="vlan_0"))
#     await db.commit()
#     response = await ext_client.put(
#         "/api/v1.0/groups/group0",
#         json={"name": "group2", "fieldname": "vlan", "condition": "vlan_11"},
#     )

#     res_json = response.json()
#     assert response.status_code == status.HTTP_200_OK
#     assert isinstance(res_json, dict)
#     assert "group2" == res_json.get("name")


# async def test_v1_group_delete_name(db: AsyncSession, ext_client: AsyncClient) -> None:
#     # Create entry in db
#     db.add(Group(name="group01", fieldname="vlan", condition="vlan_01"))
#     await db.commit()
#     response = await ext_client.delete(
#         "/api/v1.0/groups/group01",
#     )

#     assert response.status_code == status.HTTP_204_NO_CONTENT

#     # Entry is not found in db.
#     assert (
#         await db.execute(select(Group).where(Group.name == "group01"))
#     ).scalar_one_or_none() is None
