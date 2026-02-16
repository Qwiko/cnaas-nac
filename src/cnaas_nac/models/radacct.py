import datetime
from typing import Any, Optional

from pydantic import AwareDatetime, IPvAnyAddress
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .base import Base


class RadAcct(Base):
    __tablename__ = "radacct"
    __table_args__ = (
        PrimaryKeyConstraint("radacctid", name="radacct_pkey"),
        UniqueConstraint("acctuniqueid", name="radacct_acctuniqueid_key"),
        Index("radacct_active_session_idx", "acctuniqueid"),
        Index("radacct_bulk_close", "nasipaddress", "acctstarttime"),
        Index("radacct_bulk_timeout", Column("acctstoptime").nullsfirst(), "acctupdatetime"),
        Index("radacct_start_user_idx", "acctstarttime", "username"),
    )

    radacctid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    acctsessionid: Mapped[str] = mapped_column(Text, nullable=False)
    acctuniqueid: Mapped[str] = mapped_column(Text, nullable=False)
    nasipaddress: Mapped[Any] = mapped_column(INET, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(Text)
    groupname: Mapped[Optional[str]] = mapped_column(Text)
    realm: Mapped[Optional[str]] = mapped_column(Text)
    nasportid: Mapped[Optional[str]] = mapped_column(Text)
    nasporttype: Mapped[Optional[str]] = mapped_column(Text)
    acctstarttime: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    acctupdatetime: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    acctstoptime: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    acctinterval: Mapped[Optional[int]] = mapped_column(BigInteger)
    acctsessiontime: Mapped[Optional[int]] = mapped_column(BigInteger)
    acctauthentic: Mapped[Optional[str]] = mapped_column(Text)
    connectinfo_start: Mapped[Optional[str]] = mapped_column(Text)
    connectinfo_stop: Mapped[Optional[str]] = mapped_column(Text)
    acctinputoctets: Mapped[Optional[int]] = mapped_column(BigInteger)
    acctoutputoctets: Mapped[Optional[int]] = mapped_column(BigInteger)
    calledstationid: Mapped[Optional[str]] = mapped_column(Text)
    callingstationid: Mapped[Optional[str]] = mapped_column(Text)
    acctterminatecause: Mapped[Optional[str]] = mapped_column(Text)
    servicetype: Mapped[Optional[str]] = mapped_column(Text)
    framedprotocol: Mapped[Optional[str]] = mapped_column(Text)
    framedipaddress: Mapped[Optional[Any]] = mapped_column(INET)
    framedipv6address: Mapped[Optional[Any]] = mapped_column(INET)
    framedipv6prefix: Mapped[Optional[Any]] = mapped_column(INET)
    framedinterfaceid: Mapped[Optional[str]] = mapped_column(Text)
    delegatedipv6prefix: Mapped[Optional[Any]] = mapped_column(INET)
    class_: Mapped[Optional[str]] = mapped_column("class", Text)
