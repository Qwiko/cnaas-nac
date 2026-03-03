import enum
from typing import Optional

from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    and_,
    desc,
    select,
    text,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.radacct import RadAcct
from cnaas_nac.models.radpostauth import RadPostAuth

from .base import Base, TimestampsMixin


class EndpointState(str, enum.Enum):
    # MAB devices first seen in the network.
    DISCOVERED = "discovered"
    # Users which does not pass any policy
    # If discovered it will stay in discovered
    # If authorized and stops being authorized it will be set to rejected
    REJECTED = "rejected"

    PENDING = (
        "pending"  # When Updated/Created via the API, will be updated next auth try
    )

    AUTHORIZED = "authorized"  # Passed policy engine, accepted onto the network


class EndpointGroup(Base, TimestampsMixin):
    __tablename__ = "endpoint_group"
    __table_args__ = (UniqueConstraint("name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text"), index=True
    )

    # The relationship to the Endpoint model
    endpoints: Mapped[list["Endpoint"]] = relationship(back_populates="group")


class Endpoint(Base, TimestampsMixin):
    __tablename__ = "endpoint"
    __table_args__ = (UniqueConstraint("username", "calling_station_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # These two fields together are the unique identifier.
    # One EAP username could have multiple devices(calling_stations_ids).
    username: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text"), index=True
    )
    calling_station_id: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text"), index=True
    )

    state: Mapped[EndpointState] = mapped_column(Enum(EndpointState))

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optional static group assignment
    # This is only possible for mac usernames ie MAB clients.
    # MAB clients that does not match any policy will be created without any group with state: DISCOVERED
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("endpoint_group.id", name="fk_endpoint_group_id"), nullable=True
    )

    group: Mapped[Optional["EndpointGroup"]] = relationship(back_populates="endpoints")

    @hybrid_property
    def nas_identifier(self) -> Optional[str]:
        if self.nasports:
            return self.nasports[0].nas_identifier
        return None

    @nas_identifier.expression  # type: ignore[no-redef]
    def nas_identifier(cls):
        return (
            select(NasPort.nas_identifier)
            .where(
                and_(
                    NasPort.username == cls.username,
                    NasPort.calling_station_id == cls.calling_station_id,
                )
            )
            .order_by(NasPort.updated_at.desc())
            .limit(1)
            .correlate(cls)
            .scalar_subquery()
        )

    @hybrid_property
    def nas_port_id(self) -> Optional[str]:
        if self.nasports:
            return self.nasports[0].nas_port_id
        return None

    @nas_port_id.expression  # type: ignore[no-redef]
    def nas_port_id(cls):
        return (
            select(NasPort.nas_port_id)
            .where(
                and_(
                    NasPort.username == cls.username,
                    NasPort.calling_station_id == cls.calling_station_id,
                )
            )
            .order_by(NasPort.updated_at.desc())
            .limit(1)
            .correlate(cls)
            .scalar_subquery()
        )

    nasports: Mapped[list["NasPort"]] = relationship(
        primaryjoin=and_(
            username == foreign(NasPort.username),
            calling_station_id == foreign(NasPort.calling_station_id),
        ),
        lazy="selectin",
        foreign_keys="[NasPort.username, NasPort.calling_station_id]",
        cascade="all, delete-orphan",
        order_by=desc(NasPort.updated_at),
    )

    radaccts: Mapped[list["RadAcct"]] = relationship(
        primaryjoin=and_(
            username == foreign(RadAcct.username),
            calling_station_id == foreign(RadAcct.calling_station_id),
        ),
        foreign_keys="[RadAcct.username, RadAcct.calling_station_id]",
        cascade="all, delete-orphan",
    )

    radpostauths: Mapped[list["RadPostAuth"]] = relationship(
        primaryjoin=and_(
            username == foreign(RadPostAuth.username),
            calling_station_id == foreign(RadPostAuth.calling_station_id),
        ),
        foreign_keys="[RadPostAuth.username, RadPostAuth.calling_station_id]",
        cascade="all, delete-orphan",
    )
