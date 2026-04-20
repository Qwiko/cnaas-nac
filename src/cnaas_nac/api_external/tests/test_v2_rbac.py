import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.endpoint import EndpointGroup
from cnaas_nac.models.rbac import RBAC, RBACPermission

pytestmark = pytest.mark.anyio


async def test_v2_rbac_get_notfound(db: AsyncSession, ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/rbac",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_v2_rbac_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    endpoint_groups = []
    for i in range(3):
        endpoint_group = EndpointGroup(name=f"Group {i}")
        endpoint_groups.append(endpoint_group)
        db.add(endpoint_group)

    db.add(
        RBAC(
            name="test",
            allowed_endpoint_groups=endpoint_groups,
            permissions=[RBACPermission(resource="endpoint", methods=["GET", "POST"])],
        )
    )
    await db.commit()

    response = await ext_client.get(
        "/api/v2/rbac",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test"
    assert data[0]["allowed_endpoint_groups"] == [eg.id for eg in endpoint_groups]
    assert len(data[0]["permissions"]) == 1
    assert data[0]["permissions"][0]["resource"] == "endpoint"
    assert set(data[0]["permissions"][0]["methods"]) == {"GET", "POST"}


async def test_v2_rbac_delete(db: AsyncSession, ext_client: AsyncClient) -> None:
    rbac = RBAC(
        name="test",
        allowed_endpoint_groups=[],
        permissions=[RBACPermission(resource="endpoint", methods=["GET", "POST"])],
    )
    db.add(rbac)
    await db.commit()

    response = await ext_client.delete(
        f"/api/v2/rbac/{rbac.id}",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify that the RBAC entry has been deleted from the database
    db_data = await db.execute(select(RBAC))

    assert db_data.scalars().first() is None


async def test_v2_rbac_delete_notfound(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    response = await ext_client.delete(
        "/api/v2/rbac/9999",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "RBAC not found"}


async def test_v2_rbac_create(db: AsyncSession, ext_client: AsyncClient) -> None:
    endpoint_groups = []
    for i in range(3):
        endpoint_group = EndpointGroup(name=f"Group {i}")
        endpoint_groups.append(endpoint_group)
        db.add(endpoint_group)
    await db.commit()

    response = await ext_client.post(
        "/api/v2/rbac",
        json={
            "name": "test",
            "allowed_endpoint_groups": [eg.id for eg in endpoint_groups],
            "permissions": [{"resource": "endpoint", "methods": ["GET", "POST"]}],
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["name"] == "test"
    assert data["allowed_endpoint_groups"] == [eg.id for eg in endpoint_groups]
    assert len(data["permissions"]) == 1
    assert data["permissions"][0]["resource"] == "endpoint"
    assert set(data["permissions"][0]["methods"]) == {"GET", "POST"}


async def test_v2_rbac_create_resource_unique(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    """Resource needs to be unique between the permissions"""
    response = await ext_client.post(
        "/api/v2/rbac",
        json={
            "name": "test",
            "allowed_endpoint_groups": [],
            "permissions": [
                {"resource": "endpoint", "methods": ["GET", "POST"]},
                {"resource": "endpoint", "methods": ["GET"]},
            ],
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_v2_rbac_update_notfound(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    response = await ext_client.put(
        "/api/v2/rbac/9999",
        json={
            "name": "updated",
            "allowed_endpoint_group_ids": [4, 5, 6],
            "permissions": [{"resource": "endpoint", "methods": ["PUT"]}],
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "RBAC not found"}


async def test_v2_rbac_update(db: AsyncSession, ext_client: AsyncClient) -> None:
    rbac = RBAC(
        name="test",
        allowed_endpoint_groups=[],
        permissions=[RBACPermission(resource="endpoint", methods=["GET", "POST"])],
    )
    db.add(rbac)

    endpoint_group = EndpointGroup(name="Group 1")
    db.add(endpoint_group)
    await db.commit()

    response = await ext_client.put(
        f"/api/v2/rbac/{rbac.id}",
        json={
            "name": "updated",
            "allowed_endpoint_groups": [endpoint_group.id],
            "permissions": [{"resource": "endpoint", "methods": ["PUT"]}],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["name"] == "updated"
    assert data["allowed_endpoint_groups"] == [endpoint_group.id]
    assert len(data["permissions"]) == 1
    assert data["permissions"][0]["resource"] == "endpoint"
    assert set(data["permissions"][0]["methods"]) == {"PUT"}
