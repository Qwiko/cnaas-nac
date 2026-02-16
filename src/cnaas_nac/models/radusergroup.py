from typing import Any, Optional
import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, PrimaryKeyConstraint, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .base import Base

class RadUserGroup(Base):
    __tablename__ = 'radusergroup'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='radusergroup_pkey'),
        Index('radusergroup_username', 'username')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    groupname: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
