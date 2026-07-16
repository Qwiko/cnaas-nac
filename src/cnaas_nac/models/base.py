from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampsMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(True), server_default=func.now(), nullable=False, index=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
