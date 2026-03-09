# from enum import Enum
from enum import Enum
from typing import Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings


class EnvironmentOption(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    POSTGRES_USER: str = "cnaas"
    POSTGRES_PASSWORD: str = "cnaas"
    POSTGRES_SERVER: str = "nac_postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "nac"

    POSTGRES_SYNC_PREFIX: str = "postgresql://"
    POSTGRES_ASYNC_PREFIX: str = "postgresql+asyncpg://"

    POSTGRES_URL: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def POSTGRES_URI(self) -> str:
        return f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    RADIUS_COA_ENABLED: bool = True
    RADIUS_COA_SECRET: str = "testing123"

    OIDC_CLIENT_ID: str = "cnaas-nac"
    OIDC_CLIENT_SECRET: str = ""
    OIDC_DISCOVERY_URL: str = ""
    OIDC_USERNAME_ATTRIBUTE: str = "preferred_username"

    SECRET_KEY: str = "replace_this_with_a_secure_random_string"

    FRONTEND_CALLBACK_URL: str = "/#/auth-callback"

    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL


settings = Settings()
