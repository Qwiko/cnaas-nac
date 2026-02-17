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


class RadPostAuth(Base):
    __tablename__ = "radpostauth"
    __table_args__ = (PrimaryKeyConstraint("id", name="radpostauth_pkey"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    authdate: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    pass_: Mapped[Optional[str]] = mapped_column("pass", Text)
    reply: Mapped[Optional[str]] = mapped_column(Text)
    calledstationid: Mapped[Optional[str]] = mapped_column(Text)
    callingstationid: Mapped[Optional[str]] = mapped_column(Text)
    class_: Mapped[Optional[str]] = mapped_column("class", Text)
    
    # Custom nac fields
    reply_message: Mapped[Optional[str]] = mapped_column(Text)
