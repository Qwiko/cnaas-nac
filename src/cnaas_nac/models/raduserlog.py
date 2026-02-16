import datetime
import enum

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    Unicode,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AuthStatus(enum.Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    ERROR = "error"


class RadUserLog(Base):
    __tablename__ = "raduserlog"
    __table_args__ = (
        None,
        UniqueConstraint("id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(Unicode(64), nullable=False, index=True)

    status: Mapped[AuthStatus] = mapped_column(
        Enum(AuthStatus), nullable=False, index=True
    )

    reason: Mapped[str] = mapped_column(Unicode(256))

    calling_station_id: Mapped[str] = mapped_column(
        Unicode(64), index=True
    ) 
    nas_ip_address: Mapped[str] = mapped_column(
        Unicode(64)
    )

    # Timestamps (Use timezone-aware UTC)
    authdate: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Optional: Store the raw request/response for deep debugging
    # comment = Column(Unicode(512))
