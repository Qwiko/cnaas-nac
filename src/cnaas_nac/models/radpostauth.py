import datetime
from typing import Any, Optional

from pydantic import IPvAnyAddress
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RadPostAuth(Base):
    __tablename__ = "radpostauth"
    __table_args__ = (
        PrimaryKeyConstraint("id"),
        Index(
            "ix_radpostauth_username_calling_station_id",
            "username",
            "calling_station_id",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    calling_station_id: Mapped[str] = mapped_column(Text)

    auth_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    pass_: Mapped[Optional[str]] = mapped_column("pass", Text)
    reply: Mapped[Optional[str]] = mapped_column(Text)
    called_station_id: Mapped[Optional[str]] = mapped_column(Text)
    nas_ip_address: Mapped[IPvAnyAddress] = mapped_column(INET, nullable=False)

    request_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    reply_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    matched_policy_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("policy.id", name="fk_policy_id"), nullable=True
    )

    error_message: Mapped[Optional[str]] = mapped_column(Text)
    nas_identifier: Mapped[str] = mapped_column(Text, nullable=True)
    nas_port_id: Mapped[Optional[str]] = mapped_column(Text)

    class_: Mapped[Optional[str]] = mapped_column("class", Text)
