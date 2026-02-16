# from enum import Enum
from typing import Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    RADIUS_SLAVE: bool = False
    RADIUS_COA_SECRET: str = "testing123"
    RADIUS_LOCK_VLANS: list[int] = []
    RADIUS_DEFAULT_VLAN: int = 13


class PostgresSettings(BaseSettings):
    POSTGRES_USER: str = "cnaas"
    POSTGRES_PASSWORD: str = "cnaas"
    POSTGRES_SERVER: str = "nac_postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "nac"
    POSTGRES_SYNC_PREFIX: str = "postgresql://"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"

    POSTGRES_URL: Optional[str] = None

    @computed_field
    @property
    def POSTGRES_URI(self) -> str:
        return f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


# class EnvironmentOption(Enum):
#     LOCAL = "local"
#     STAGING = "staging"
#     PRODUCTION = "production"


# class EnvironmentSettings(BaseSettings):
#     ENVIRONMENT: EnvironmentOption = "local"


class Settings(
    AppSettings,
    PostgresSettings,
    # EnvironmentSettings
):
    pass


settings = Settings()
