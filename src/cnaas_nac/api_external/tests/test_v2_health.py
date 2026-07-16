import pytest
from fastapi import status
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_v2_health(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/health",
    )

    assert response.status_code == status.HTTP_200_OK
