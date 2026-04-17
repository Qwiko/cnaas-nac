import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.rbac import RBAC, RBACPermission

pytestmark = pytest.mark.anyio


async def test_v2_rbac_get_notfound(db: AsyncSession, ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/rbac",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_v2_rbac_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    db.add(RBAC(name="test", allowed_group_ids=[1, 2, 3], permissions=[RBACPermission(path="/endpoint", methods=["GET", "POST"])]))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/rbac",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test"
    assert data[0]["allowed_group_ids"] == [1, 2, 3]
    assert len(data[0]["permissions"]) == 1
    assert data[0]["permissions"][0]["path"] == "/endpoint"
    assert set(data[0]["permissions"][0]["methods"]) ==  {"GET", "POST"}


async def test_v2_rbac_delete(db: AsyncSession, ext_client: AsyncClient) -> None:
    rbac = RBAC(name="test", allowed_group_ids=[1, 2, 3], permissions=[RBACPermission(path="/endpoint", methods=["GET", "POST"])])
    db.add(rbac)
    await db.commit()

    response = await ext_client.delete(
        f"/api/v2/rbac/{rbac.id}",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT