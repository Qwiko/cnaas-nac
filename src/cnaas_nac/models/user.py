import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign

from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.models.radpostauth import RadPostAuth

from .base import Base, TimestampsMixin


class User(Base, TimestampsMixin):
    __tablename__ = "user"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="user_pkey"),
        Index("user_username", "username"),
        UniqueConstraint("username", name="uq_username"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )

    enabled: Mapped[bool] = mapped_column(Boolean, server_default=false())

    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vlan: Mapped[int] = mapped_column(Integer, nullable=False)

    access_start: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(True), nullable=True
    )
    access_stop: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(True), nullable=True
    )

    nasports: Mapped[list["NasPort"]] = relationship(
        primaryjoin=username == foreign(NasPort.username),
        foreign_keys="[NasPort.username]",
        cascade="all, delete-orphan",
    )

    radaccts: Mapped[list["RadAcct"]] = relationship(
        primaryjoin=username == foreign(RadAcct.username),
        foreign_keys="[RadAcct.username]",
        cascade="all, delete-orphan",
    )

    radpostauths: Mapped[list["RadPostAuth"]] = relationship(
        primaryjoin=username == foreign(RadPostAuth.username),
        foreign_keys="[RadPostAuth.username]",
        cascade="all, delete-orphan",
    )
