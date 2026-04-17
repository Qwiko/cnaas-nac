import pytest
from fastapi import status
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_v2_auth_me(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/auth/me",
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "test_user_123"


async def test_v2_auth_permissions(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/auth/permissions",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert isinstance(data, dict)
