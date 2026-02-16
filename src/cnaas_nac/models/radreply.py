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
    Unicode,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .base import Base


class RadReply(Base):
    __tablename__ = "radreply"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="radreply_pkey"),
        Index("radreply_username", "username", "attribute"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
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
