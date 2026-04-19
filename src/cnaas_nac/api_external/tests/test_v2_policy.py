import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.policy import Policy


pytestmark = pytest.mark.anyio


async def test_v2_policy_get_notfound(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/policy",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_v2_policy_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    db.add(Policy(name="Policy 1", description="Test policy 1"))
    await db.commit()

    response = await ext_client.get(
        "/api/v2/policy",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Policy 1"


async def test_v2_policy_delete(db: AsyncSession, ext_client: AsyncClient) -> None:
    policy = Policy(name="Policy to delete", description="This policy will be deleted")
    db.add(policy)
    await db.commit()

    response = await ext_client.delete(
        f"/api/v2/policy/{policy.id}",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


async def test_v2_policy_delete_notfound(ext_client: AsyncClient) -> None:
    response = await ext_client.delete(
        "/api/v2/policy/9999",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
