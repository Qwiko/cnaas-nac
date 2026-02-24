import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    PrimaryKeyConstraint,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RadPostAuth(Base):
    __tablename__ = "radpostauth"
    __table_args__ = (PrimaryKeyConstraint("id", name="radpostauth_pkey"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    auth_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
    pass_: Mapped[Optional[str]] = mapped_column("pass", Text)
    reply: Mapped[Optional[str]] = mapped_column(Text)
    called_station_id: Mapped[Optional[str]] = mapped_column(Text)
    calling_station_id: Mapped[Optional[str]] = mapped_column(Text)
    # Custom nac fields
    reply_message: Mapped[Optional[str]] = mapped_column(Text)
    nas_identifier: Mapped[str] = mapped_column(Text, nullable=True)
    nas_port_id: Mapped[Optional[str]] = mapped_column(Text)

    class_: Mapped[Optional[str]] = mapped_column("class", Text)
