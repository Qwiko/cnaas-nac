import datetime
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
    Unicode,
    UniqueConstraint,
    text,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampsMixin

class NasPort(Base, TimestampsMixin):
    __tablename__ = "nasport"
    __table_args__ = (
        None,
        UniqueConstraint("id"),
        UniqueConstraint(
            "username", "nas_identifier", "nas_port_id", name="uq_user_nas_port"
        ),
        UniqueConstraint(
            "username",
            "calling_station_id",
            "nas_port_id",
            name="uq_user_calling_station_port",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    username: Mapped[str] = mapped_column(Unicode(64), nullable=False, index=True)
    nas_identifier: Mapped[Optional[str]] = mapped_column(Unicode(64), nullable=False)
    nas_port_id: Mapped[Optional[str]] = mapped_column(Unicode(64), nullable=False)
    nas_ip_address: Mapped[Optional[str]] = mapped_column(Unicode(64), nullable=False)
    calling_station_id: Mapped[Optional[str]] = mapped_column(
        Unicode(64), nullable=False
    )
    called_station_id: Mapped[Optional[str]] = mapped_column(
        Unicode(64), nullable=False
    )

    @hybrid_property
    def last_seen(self) -> datetime.datetime:
        return self.updated_at
