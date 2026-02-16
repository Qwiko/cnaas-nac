import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.oui import DeviceOui
from cnaas_nac.models.radreply import RadReply

pytestmark = pytest.mark.anyio


async def test_v2_vlans_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    for i in range(10, 100):
        db.add(
            RadReply(
                username=f"00:00:00:00:00:{hex(i)[2:4]}",
                attribute="Tunnel-Private-Group-Id",
                op=":=",
                value=str(i),
            )
        )
    await db.commit()

    response = await ext_client.get(
        "/api/v2/vlans",
    )

    res_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) >= 90

async def test_v2_vlans_get_notfound(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Remove all replies if there are any in test-db
    # Will be brought back by a transaction.
    
    await db.execute(delete(RadReply))
    
    response = await ext_client.get(
        "/api/v2/vlans",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_v2_vlans_get_id(db: AsyncSession, ext_client: AsyncClient) -> None:
    for i in range(10, 100):
        db.add(
            RadReply(
                username=f"00:00:00:00:00:{hex(i)[2:4]}",
                attribute="Tunnel-Private-Group-Id",
                op=":=",
                value="1313",
            )
        )
    await db.commit()

    response = await ext_client.get(
        "/api/v2/vlans/1313",
    )

    res_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) >= 90


async def test_v2_vlans_get_id_notfound(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/vlans/111",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
