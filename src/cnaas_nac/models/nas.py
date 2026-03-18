import datetime
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    Integer,
    PrimaryKeyConstraint,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import CIDR
from pydantic.networks import IPvAnyNetwork
from .base import Base, TimestampsMixin


class Nas(Base, TimestampsMixin):
    __tablename__ = "nas"
    __table_args__ = (PrimaryKeyConstraint("id", name="nas_pkey"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    network: Mapped[IPvAnyNetwork] = mapped_column(CIDR, index=True, unique=True)

    type: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'other'::text")
    )
    secret: Mapped[str] = mapped_column(Text, nullable=False)
    server: Mapped[Optional[str]] = mapped_column(Text)
    require_ma: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'auto'::text")
    )
    limit_proxy_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'auto'::text")
    )
    # ports: Mapped[Optional[int]] = mapped_column(Integer)


class NasReload(Base):
    __tablename__ = "nasreload"
    __table_args__ = (PrimaryKeyConstraint("nasipaddress", name="nasreload_pkey"),)

    nasipaddress: Mapped[Any] = mapped_column(INET, primary_key=True)
    reloadtime: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False
    )
