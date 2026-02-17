from sqlalchemy import Integer, Unicode, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from cnaas_nac.models.base import Base


class DeviceOui(Base):
    __tablename__ = "device_oui"
    __table_args__ = (
        None,
        UniqueConstraint("id"),
        UniqueConstraint("oui"),
    )

    id: Mapped[int] = mapped_column(
        Integer, autoincrement=True, primary_key=True, index=True
    )
    oui: Mapped[str] = mapped_column(Unicode(64), nullable=False)
    vlan: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Unicode(64), nullable=True)
