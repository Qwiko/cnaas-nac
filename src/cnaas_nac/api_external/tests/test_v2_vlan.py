import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from cnaas_nac.models.user import User

pytestmark = pytest.mark.anyio


async def test_v2_vlans_get(db: AsyncSession, ext_client: AsyncClient) -> None:
    for i in range(10, 100):
        db.add(
            User(
                username=f"00:00:00:00:00:{hex(i)[2:4]}",
                vlan=i,
                enabled=True,
            )
        )
    await db.commit()

    response = await ext_client.get(
        "/api/v2/vlan",
    )

    res_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) >= 90


async def test_v2_vlans_get_notfound(db: AsyncSession, ext_client: AsyncClient) -> None:
    # Remove all Users if there are any in test-db
    # Will be brought back by a transaction.

    await db.execute(delete(User))

    response = await ext_client.get(
        "/api/v2/vlan",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_v2_vlans_get_id(db: AsyncSession, ext_client: AsyncClient) -> None:
    for i in range(10, 100):
        db.add(
            User(
                username=f"00:00:00:00:00:{hex(i)[2:4]}",
                vlan=1313,
                enabled=True,
            )
        )
    await db.commit()

    response = await ext_client.get(
        "/api/v2/vlan/1313",
    )

    res_json = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(res_json, list)
    assert len(res_json) >= 90


async def test_v2_vlans_get_id_notfound(ext_client: AsyncClient) -> None:
    response = await ext_client.get(
        "/api/v2/vlan/111",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
