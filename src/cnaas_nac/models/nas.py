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
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampsMixin


class Nas(Base):
    __tablename__ = "nas"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="nas_pkey"),
        Index("nas_nasname", "nasname"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nasname: Mapped[str] = mapped_column(Text, nullable=False)
    shortname: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'other'::text")
    )
    secret: Mapped[str] = mapped_column(Text, nullable=False)
    require_ma: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'auto'::text")
    )
    limit_proxy_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'auto'::text")
    )
    ports: Mapped[Optional[int]] = mapped_column(Integer)
    server: Mapped[Optional[str]] = mapped_column(Text)
    community: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)


class NasReload(Base):
    __tablename__ = "nasreload"
    __table_args__ = (PrimaryKeyConstraint("nasipaddress", name="nasreload_pkey"),)

    nasipaddress: Mapped[Any] = mapped_column(INET, primary_key=True)
    reloadtime: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False
    )


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
