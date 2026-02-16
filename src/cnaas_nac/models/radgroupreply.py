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


class RadGroupReply(Base):
    __tablename__ = "radgroupreply"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="radgroupreply_pkey"),
        Index("radgroupreply_groupname", "groupname", "attribute"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    groupname: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )
    attribute: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )
    op: Mapped[str] = mapped_column(
        String(2), nullable=False, server_default=text("'='::character varying")
    )
    value: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )
