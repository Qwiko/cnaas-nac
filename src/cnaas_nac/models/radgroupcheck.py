from sqlalchemy import (
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from cnaas_nac.models.base import Base


class RadGroupCheck(Base):
    __tablename__ = "radgroupcheck"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="radgroupcheck_pkey"),
        Index("radgroupcheck_groupname", "groupname", "attribute"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    groupname: Mapped[str] = mapped_column(
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
