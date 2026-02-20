# from enum import Enum
from enum import Enum
from typing import Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    RADIUS_SLAVE: bool = False
    RADIUS_LOCK_VLANS: list[int] = []
    RADIUS_DEFAULT_VLAN: int = 13

    SECRET_KEY: str = "replace_this_with_a_secure_random_string"

    FRONTEND_CALLBACK_URL: Optional[str] = "/"
    # OpenID Connect Settings
    OIDC_CLIENT_ID: Optional[str] = "cnaas-nac"
    OIDC_CLIENT_SECRET: Optional[str] = "1Y6VUdjVpE7irdetMBQvJGQ7SywNWGqW"
    # The URL that ends in .well-known/openid-configuration
    # e.g.,
    OIDC_DISCOVERY_URL: Optional[str] = (
        "http://localhost:8080/realms/master/.well-known/openid-configuration"
    )
    OIDC_USERNAME_ATTRIBUTE: Optional[str] = "preferred_username"


class RadiusCoASettings(BaseSettings):
    RADIUS_COA_ENABLED: bool = True
    RADIUS_COA_SECRET: str = "testing123"


class PostgresSettings(BaseSettings):
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


class EnvironmentOption(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentSettings(BaseSettings):
    ENVIRONMENT: EnvironmentOption = "local"


class Settings(AppSettings, RadiusCoASettings, PostgresSettings, EnvironmentSettings):
    pass


settings = Settings()
