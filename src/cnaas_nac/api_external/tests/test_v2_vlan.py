import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.policy import PolicyReply

pytestmark = pytest.mark.anyio


async def test_v2_vlans_get_notfound(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Remove all Users if there are any in test-db
    # Will be brought back by a transaction.

    await db.execute(delete(PolicyReply))

    response = await ext_client.get(
        "/api/v2/vlan",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
