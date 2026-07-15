import enum

from sqlalchemy import (
    Enum,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from cnaas_nac.models.base import Base, TimestampsMixin


class RadiusCommand(str, enum.Enum):
    CLEAR_CLIENT = "clear_client"
    DEBUG_START = "debug_start"
    DEBUG_STOP = "debug_stop"
    DEBUG_CLEAR = "debug_clear"


class RadiusAdminEvent(Base, TimestampsMixin):
    __tablename__ = "radius_admin_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    command: Mapped[RadiusCommand] = mapped_column(Enum(RadiusCommand), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=True)


class RadiusDebugLog(Base):
    __tablename__ = "radius_debug_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    node_name: Mapped[str] = mapped_column(String(50), nullable=False)

    log_line: Mapped[str] = mapped_column(Text, nullable=False)
