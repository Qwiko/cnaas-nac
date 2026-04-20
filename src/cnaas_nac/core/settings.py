# from enum import Enum
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings

import logging


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
    OIDC_USERINFO_ATTRIBUTE: str = "userinfo"
    OIDC_USERNAME_ATTRIBUTE: str = "preferred_username"
    OIDC_GROUPS_ATTRIBUTE: str = "roles"
    OIDC_ADMIN_GROUP: str = "admins"

    SECRET_KEY: str = "replace_this_with_a_secure_random_string"
    JWT_EXPIRATION_MINUTES: int = 60

    FRONTEND_CALLBACK_URL: str = "/#/auth-callback"

    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL

    PRUNING_DISABLED: bool = False

    ENDPOINT_MAB_DISCOVERED_RETENTION_DAYS: Annotated[int, Field(gt=0)] = 30
    ENDPOINT_MAB_PENDING_RETENTION_DAYS: Annotated[int, Field(gt=0)] = 30

    ENDPOINT_MAB_REJECTED_RETENTION_DAYS: Annotated[int, Field(gt=0)] = 30
    ENDPOINT_EAP_REJECTED_RETENTION_DAYS: Annotated[int, Field(gt=0)] = 30

    ENDPOINT_MAB_AUTHORIZED_RETENTION_DAYS: Annotated[int, Field(gt=0)] = 90
    ENDPOINT_EAP_AUTHORIZED_RETENTION_DAYS: Annotated[int, Field(gt=0)] = 90

    RADACCT_RETENTION_DAYS: Annotated[int, Field(gt=0)] = 90
    RADPOSTAUTH_RETENTION_DAYS: Annotated[int, Field(gt=0)] = 90

    LOGGING: str | int = logging.INFO

    @field_validator("LOGGING", mode="before")
    @classmethod
    def setup_logging(cls, v: Any) -> int:
        if not v:
            return logging.INFO
        if v not in logging._nameToLevel:
            return logging.INFO
        return logging._nameToLevel.get(v, logging.INFO)


settings = Settings()
