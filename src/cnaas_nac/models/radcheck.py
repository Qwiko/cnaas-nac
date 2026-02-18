import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from cnaas_nac.models.nas import NasPort
from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.models.radpostauth import RadPostAuth
from cnaas_nac.models.radusergroup import RadUserGroup

from .base import Base, TimestampsMixin
from .radreply import RadReply


class RadCheck(Base, TimestampsMixin):
    __tablename__ = "radcheck"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="radcheck_pkey"),
        # Index("radcheck_username", "username", "attribute"),
        UniqueConstraint("username", name="uq_username"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )

    # FreeRadius tables that we dont use.
    # We user radcheck as a users table instead.
    # attribute: Mapped[str] = mapped_column(
    #     Text, nullable=False, server_default=text("''::text")
    # )
    # op: Mapped[str] = mapped_column(
    #     String(2), nullable=False, server_default=text("'=='::character varying")
    # )
    # value: Mapped[str] = mapped_column(
    #     Text, nullable=False, server_default=text("''::text")
    # )

    enabled: Mapped[bool] = mapped_column(Boolean, server_default=false())

    comment: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, server_default=text("''::text")
    )

    access_start: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(True), nullable=True
    )
    access_stop: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(True), nullable=True
    )

    nasports: Mapped[list["NasPort"]] = relationship(
        primaryjoin="RadCheck.username == NasPort.username",
        foreign_keys="NasPort.username",
        cascade="all, delete-orphan",
    )

    radaccts: Mapped[list["RadAcct"]] = relationship(
        primaryjoin="RadCheck.username == RadAcct.username",
        foreign_keys="RadAcct.username",
        cascade="all, delete-orphan",
    )

    radreplies: Mapped[list["RadReply"]] = relationship(
        primaryjoin="RadCheck.username == RadReply.username",
        foreign_keys="RadReply.username",
        cascade="all, delete-orphan",
    )

    radusergroups: Mapped[list["RadUserGroup"]] = relationship(
        primaryjoin="RadCheck.username == RadUserGroup.username",
        foreign_keys="RadUserGroup.username",
        cascade="all, delete-orphan",
    )

    radpostauths: Mapped[list["RadPostAuth"]] = relationship(
        primaryjoin="RadCheck.username == RadPostAuth.username",
        foreign_keys="RadPostAuth.username",
        cascade="all, delete-orphan",
    )
