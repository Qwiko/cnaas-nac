import datetime
from typing import Optional

from sqlalchemy import (
    Index,
    Integer,
    Unicode,
    UniqueConstraint,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampsMixin


class NasPort(Base, TimestampsMixin):
    __tablename__ = "nasport"
    __table_args__ = (
        None,
        UniqueConstraint("id"),
        UniqueConstraint(
            "username",
            "calling_station_id",
            "nas_identifier",
            "nas_port_id",
        ),
        UniqueConstraint(
            "username",
            "calling_station_id",
            "called_station_id",
            "nas_port_id",
            name="uq_user_called_station_port",
        ),
        Index(
            "ix_nasport_username_calling_station_id", "username", "calling_station_id"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer, autoincrement=True, primary_key=True, index=True
    )
    username: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    calling_station_id: Mapped[str] = mapped_column(Unicode(64))

    nas_identifier: Mapped[Optional[str]] = mapped_column(Unicode(64), nullable=False)
    nas_port_id: Mapped[Optional[str]] = mapped_column(Unicode(64), nullable=False)
    nas_ip_address: Mapped[Optional[str]] = mapped_column(Unicode(64), nullable=False)

    called_station_id: Mapped[Optional[str]] = mapped_column(
        Unicode(64), nullable=False
    )

    @hybrid_property
    def last_seen(self) -> datetime.datetime:
        return self.updated_at
