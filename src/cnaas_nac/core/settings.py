# from enum import Enum
from enum import Enum
from typing import Optional

from pydantic import computed_field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseModel):
    USER: str = "cnaas"
    PASSWORD: str = "cnaas"
    SERVER: str = "nac_postgres"
    PORT: int = 5432
    DB: str = "nac"

    SYNC_PREFIX: str = "postgresql://"
    ASYNC_PREFIX: str = "postgresql+asyncpg://"

    URL: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def URI(self) -> str:
        return f"{self.USER}:{self.PASSWORD}@{self.SERVER}:{self.PORT}/{self.DB}"


class RadiusSettings(BaseModel):
    SLAVE: bool = False
    LOCK_VLANS: list[int] = []
    DEFAULT_VLAN: int = 13

    COA_ENABLED: bool = True
    COA_SECRET: str = "testing123"


class OIDCSettings(BaseModel):
    CLIENT_ID: str = "cnaas-nac"
    CLIENT_SECRET: str = ""
    DISCOVERY_URL: str = ""
    USERNAME_ATTRIBUTE: str = "preferred_username"


class EnvironmentOption(Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="_", nested_model_default_partial_update=True
    )

    DB: DBSettings = DBSettings()
    RADIUS: RadiusSettings = RadiusSettings()
    OIDC: OIDCSettings = OIDCSettings()

    SECRET_KEY: str = "replace_this_with_a_secure_random_string"

    FRONTEND_CALLBACK_URL: str = "/"

    ENVIRONMENT: EnvironmentOption = EnvironmentOption.LOCAL


settings = Settings()
