from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    AsyncTransaction,
    async_sessionmaker,
    create_async_engine,
)

from cnaas_nac.api_external.main import app as external_app
from cnaas_nac.api_internal.main import app as internal_app
from cnaas_nac.core.db import get_async_session
from cnaas_nac.core.settings import EnvironmentOption, settings

async_engine = create_async_engine(
    settings.DB.ASYNC_PREFIX + settings.DB.URI, future=True
)
async_session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def connection(anyio_backend) -> AsyncGenerator[AsyncConnection, None]:
    async with async_engine.connect() as connection:
        yield connection


@pytest.fixture()
async def transaction(
    connection: AsyncConnection,
) -> AsyncGenerator[AsyncTransaction, None]:
    async with connection.begin() as transaction:
        yield transaction

        # Rollback for db, ext_client and int_client.
        await transaction.rollback()


@pytest.fixture()
async def db(
    connection: AsyncConnection, transaction: AsyncTransaction
) -> AsyncGenerator[AsyncSession, None]:
    async_session = AsyncSession(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )

    yield async_session


@pytest.fixture()
async def ext_client(
    connection: AsyncConnection, transaction: AsyncTransaction
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async_session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        async with async_session:
            yield async_session

    external_app.dependency_overrides[get_async_session] = override_get_async_session
    test_token = create_test_token()
    async with AsyncClient(
        transport=ASGITransport(app=external_app),
        base_url="http://cnaas-nac-external",
        headers={"Authorization": f"Bearer {test_token}"},
    ) as ac:
        yield ac
    external_app.dependency_overrides.clear()


@pytest.fixture()
async def int_client(
    connection: AsyncConnection, transaction: AsyncTransaction
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async_session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        async with async_session:
            yield async_session

    internal_app.dependency_overrides[get_async_session] = override_get_async_session
    async with AsyncClient(
        transport=ASGITransport(app=internal_app), base_url="http://cnaas-nac-internal"
    ) as ac:
        yield ac

    internal_app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_pydantic_settings(monkeypatch):
    """
    Automatically mock specific Pydantic settings for all tests.
    """
    # Make sure ENVIRONMENT is set to Local for tests.
    monkeypatch.setattr(settings, "ENVIRONMENT", EnvironmentOption.LOCAL)


def create_test_token() -> str:
    """Generates a test JWT signed with the application's secret key."""

    payload = {
        "sub": "test_user_123",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "email": "test@example.com",
        "preferred_username": "test@example.com",
        "groups": ["admin"],
    }

    # Encode the token using your secret key and the HS256 algorithm
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return token
