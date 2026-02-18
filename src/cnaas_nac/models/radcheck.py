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
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign

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

    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    radreplies: Mapped[list["RadReply"]] = relationship(
        primaryjoin=username == foreign(RadReply.username),
        foreign_keys="[RadReply.username]",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    radusergroups: Mapped[list["RadUserGroup"]] = relationship(
        primaryjoin=username == foreign(RadUserGroup.username),
        foreign_keys="[RadUserGroup.username]",
        cascade="all, delete-orphan",
    )

    radpostauths: Mapped[list["RadPostAuth"]] = relationship(
        primaryjoin=username == foreign(RadPostAuth.username),
        foreign_keys="[RadPostAuth.username]",
        cascade="all, delete-orphan",
    )

    @property
    def vlan(self) -> Optional[int]:
        """
        Gets the VLAN ID (Tunnel-Private-Group-Id) from RadReply.
        """
        for reply in self.radreplies:
            if reply.attribute == "Tunnel-Private-Group-Id":
                return int(reply.value)
        return None

    @vlan.setter
    def vlan(self, vlan_id: str | int | None):
        """
        Sets or updates the VLAN ID in RadReply.
        If set to None, the specific RadReply entry is removed.
        """
        target_attribute = "Tunnel-Private-Group-Id"

        # 1. Search for existing entry
        existing_reply = next(
            (r for r in self.radreplies if r.attribute == target_attribute), None
        )

        # 2. Case: Remove the VLAN (set to None)
        if vlan_id is None:
            if existing_reply:
                self.radreplies.remove(existing_reply)
            return

        # 3. Case: Update or Create
        str_value = str(vlan_id)

        if existing_reply:
            # Update existing
            existing_reply.value = str_value
        else:
            # Create new. Note: 'op' usually defaults to ':=' or '=' for replies.
            # We explicitly set it to ':=' which is standard for VLAN assignment.
            new_reply = RadReply(
                username=self.username,
                attribute=target_attribute,
                op=":=",
                value=str_value,
            )
            self.radreplies.append(new_reply)
