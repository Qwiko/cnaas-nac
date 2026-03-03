import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RadAcct(Base):
    __tablename__ = "radacct"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        UniqueConstraint("acct_unique_id"),
        Index("radacct_active_session_idx", "acct_unique_id"),
        Index("radacct_bulk_close", "nas_ip_address", "acct_start_time"),
        Index(
            "radacct_bulk_timeout",
            Column("acct_stop_time").nullsfirst(),
            "acct_update_time",
        ),
        Index("radacct_start_user_idx", "acct_start_time", "username"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    acct_session_id: Mapped[str] = mapped_column(Text, nullable=False)
    acct_unique_id: Mapped[str] = mapped_column(Text, nullable=False)
    nas_ip_address: Mapped[Any] = mapped_column(INET, nullable=False)

    # cnaas-nac specific
    nas_identifier: Mapped[str] = mapped_column(Text, nullable=True)

    username: Mapped[str] = mapped_column(Text)
    calling_station_id: Mapped[str] = mapped_column(Text)

    group_name: Mapped[Optional[str]] = mapped_column(Text)
    realm: Mapped[Optional[str]] = mapped_column(Text)
    nas_port_id: Mapped[Optional[str]] = mapped_column(Text)
    nas_port_type: Mapped[Optional[str]] = mapped_column(Text)
    acct_start_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    acct_update_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(True)
    )
    acct_stop_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    acct_interval: Mapped[Optional[int]] = mapped_column(BigInteger)
    acct_session_time: Mapped[Optional[int]] = mapped_column(BigInteger)
    acct_authentic: Mapped[Optional[str]] = mapped_column(Text)
    connectinfo_start: Mapped[Optional[str]] = mapped_column(Text)
    connectinfo_stop: Mapped[Optional[str]] = mapped_column(Text)
    acct_input_octets: Mapped[Optional[int]] = mapped_column(BigInteger)
    acct_output_octets: Mapped[Optional[int]] = mapped_column(BigInteger)
    called_station_id: Mapped[Optional[str]] = mapped_column(Text)
    acct_terminate_cause: Mapped[Optional[str]] = mapped_column(Text)
    service_type: Mapped[Optional[str]] = mapped_column(Text)
    framed_protocol: Mapped[Optional[str]] = mapped_column(Text)
    framed_ip_address: Mapped[Optional[Any]] = mapped_column(INET)
    framed_ipv6_address: Mapped[Optional[Any]] = mapped_column(INET)
    framed_ipv6_prefix: Mapped[Optional[Any]] = mapped_column(INET)
    framed_interface_id: Mapped[Optional[str]] = mapped_column(Text)
    delegated_ipv6_prefix: Mapped[Optional[Any]] = mapped_column(INET)
    class_: Mapped[Optional[str]] = mapped_column("class", Text)
