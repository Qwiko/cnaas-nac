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
    and_,
    cast,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, foreign, mapped_column, relationship

from .base import Base
from .radreply import RadReply


class RadCheck(Base):
    __tablename__ = "radcheck"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="radcheck_pkey"),
        Index("radcheck_username", "username", "attribute"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )
    attribute: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )
    op: Mapped[str] = mapped_column(
        String(2), nullable=False, server_default=text("'=='::character varying")
    )
    value: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("''::text")
    )

    @hybrid_property
    def enabled(self) -> bool:
        return self.op == ":="

