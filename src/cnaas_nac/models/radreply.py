from sqlalchemy import (
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

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
