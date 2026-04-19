import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.core.security import create_access_token
from cnaas_nac.models.rbac import RBAC, RBACPermission

pytestmark = pytest.mark.anyio


async def test_v2_auth_me(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/auth/me",
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "test_user_123"


async def test_v2_auth_permissions(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/auth/permissions",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert isinstance(data, dict)


async def test_v2_auth_permissions_structure(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    rbac_entry = RBAC(
        name="group1",
        allowed_endpoint_groups=[],
        permissions=[
            RBACPermission(path="endpoint", methods=["GET", "POST"]),
        ],
    )
    db.add(rbac_entry)
    await db.commit()

    # Create a temporary jwt access token with specific groups to test the permissions endpoint

    access_token = await create_access_token(db, "test_user_123", ["group1", "group2"])

    response = await ext_client.get(
        "/api/v2/auth/permissions", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Check that the permissions structure is as expected
    assert "endpoint" in data
    assert isinstance(data["endpoint"], list)


async def test_v2_auth_no_permissions(
    db: AsyncSession, ext_client: AsyncClient
) -> None:
    rbac_entry = RBAC(
        name="group1",
        allowed_endpoint_groups=[],
        permissions=[
            RBACPermission(path="endpoint", methods=["GET", "POST"]),
        ],
    )
    db.add(rbac_entry)
    await db.commit()

    # Create a temporary jwt access token with specific groups to test the permissions endpoint

    access_token = await create_access_token(db, "test_user_123", ["group1", "group2"])

    # Can only access /endpoint.
    # other endpoints should not be in the permissions since the user doesn't have any RBAC entry granting permissions to them.
    response = await ext_client.get(
        "/api/v2/endpoint", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code != status.HTTP_403_FORBIDDEN

    for endpoint in [
        "endpoint_group",
        "policy",
        "nas_port",
        "accounting",
        "authentication",
        "radius_client",
        "vlan",
        "rbac",
    ]:
        response = await ext_client.get(
            f"/api/v2/{endpoint}", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
