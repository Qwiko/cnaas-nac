import enum

from sqlalchemy import (
    Enum,
    Integer,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from cnaas_nac.models.base import Base, TimestampsMixin


class RadiusCommand(str, enum.Enum):
    RELOAD = "reload"
    CLEAR_CLIENT = "clear_client"
    DEBUG_START = "debug_start"
    DEBUG_STOP = "debug_stop"


class RadiusAdminEvent(Base, TimestampsMixin):
    __tablename__ = "radius_admin_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    command: Mapped[RadiusCommand] = mapped_column(Enum(RadiusCommand), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=True)
