from sqlalchemy import String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from cnaas_nac.models.endpoint import EndpointGroup


class RBACEndpointGroup(Base):
    __tablename__ = "rbac_endpoint_group_association"

    rbac_id: Mapped[int] = mapped_column(ForeignKey("rbac.id"), primary_key=True)
    endpoint_group_id: Mapped[int] = mapped_column(
        ForeignKey("endpoint_group.id"), primary_key=True
    )


class RBAC(Base):
    __tablename__ = "rbac"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String, unique=True, index=True)

    allowed_endpoint_groups: Mapped[list["EndpointGroup"]] = relationship(
        secondary="rbac_endpoint_group_association", lazy="selectin"
    )

    permissions: Mapped[list["RBACPermission"]] = relationship(
        back_populates="rbac", lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def allowed_endpoint_group_ids(self) -> list[int]:
        return [endpoint_group.id for endpoint_group in self.allowed_endpoint_groups]


class RBACPermission(Base):
    __tablename__ = "rbac_permission"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("rbac.id"))

    resource: Mapped[str] = mapped_column(String)

    methods: Mapped[list[str]] = mapped_column(JSON, default=list)

    rbac: Mapped["RBAC"] = relationship(back_populates="permissions")
