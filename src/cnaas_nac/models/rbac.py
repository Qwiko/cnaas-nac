from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Group(Base):
    __tablename__ = "group"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String, unique=True, index=True)

    # TODO change to a relation to group_ids array
    allowed_groups: Mapped[list[str]] = mapped_column(JSON, default=list)

    permissions: Mapped[list["GroupPermission"]] = relationship(
        back_populates="group", lazy="selectin", cascade="all, delete-orphan"
    )


class GroupPermission(Base):
    __tablename__ = "group_permission"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))

    path: Mapped[str] = mapped_column(String)

    methods: Mapped[list[str]] = mapped_column(JSON, default=list)

    group: Mapped["Group"] = relationship(back_populates="permissions")
