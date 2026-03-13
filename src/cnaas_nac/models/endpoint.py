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
from sqlalchemy.orm import Mapped, column_property, foreign, mapped_column, relationship

from cnaas_nac.models.nas_port import NasPort
from cnaas_nac.models.radpostauth import RadPostAuth

from .base import Base, TimestampsMixin

from cnaas_nac.models.radacct import RadAcct


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

    nas_identifier: Mapped[Optional[str]] = column_property(
        select(NasPort.nas_identifier)
        .where(
            and_(
                NasPort.username == username,
                NasPort.calling_station_id == calling_station_id,
            )
        )
        .order_by(desc(NasPort.updated_at))
        .limit(1)
        .correlate_except(NasPort)
        .scalar_subquery()
    )

    nas_port_id: Mapped[Optional[str]] = column_property(
        select(NasPort.nas_port_id)
        .where(
            and_(
                NasPort.username == username,
                NasPort.calling_station_id == calling_station_id,
            )
        )
        .order_by(desc(NasPort.updated_at))
        .limit(1)
        .correlate_except(NasPort)
        .scalar_subquery()
    )

    nasports: Mapped[list["NasPort"]] = relationship(
        primaryjoin=and_(
            username == foreign(NasPort.username),
            calling_station_id == foreign(NasPort.calling_station_id),
        ),
        foreign_keys="[NasPort.username, NasPort.calling_station_id]",
        cascade="all, delete-orphan",
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


# Attact endpoint_id column_property
NasPort.endpoint_id = column_property(
    select(Endpoint.id)
    .where(
        and_(
            Endpoint.username == NasPort.username,
            Endpoint.calling_station_id == NasPort.calling_station_id,
        )
    )
    .limit(1)
    .correlate_except(Endpoint)
    .scalar_subquery()
)

NasPort.endpoint_group_id = column_property(
    select(Endpoint.group_id)
    .where(
        and_(
            Endpoint.username == NasPort.username,
            Endpoint.calling_station_id == NasPort.calling_station_id,
        )
    )
    .limit(1)
    .correlate_except(Endpoint)
    .scalar_subquery()
)

RadAcct.endpoint_id = column_property(
    select(Endpoint.id)
    .where(
        and_(
            Endpoint.username == RadAcct.username,
            Endpoint.calling_station_id == RadAcct.calling_station_id,
        )
    )
    .limit(1)
    .correlate_except(Endpoint)
    .scalar_subquery()
)

RadAcct.endpoint_group_id = column_property(
    select(Endpoint.group_id)
    .where(
        and_(
            Endpoint.username == RadAcct.username,
            Endpoint.calling_station_id == RadAcct.calling_station_id,
        )
    )
    .limit(1)
    .correlate_except(Endpoint)
    .scalar_subquery()
)

RadPostAuth.endpoint_group_id = column_property(
    select(Endpoint.group_id)
    .where(
        and_(
            Endpoint.username == RadPostAuth.username,
            Endpoint.calling_station_id == RadPostAuth.calling_station_id,
        )
    )
    .limit(1)
    .correlate_except(Endpoint)
    .scalar_subquery()
)
