import enum
from typing import List, Optional
from sqlalchemy import (
    CheckConstraint,
    String,
    Integer,
    Boolean,
    ForeignKey,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from cnaas_nac.models.endpoint import EndpointGroup
from cnaas_nac.models.radpostauth import RadPostAuth

from .base import Base, TimestampsMixin


class ClientType(enum.Enum):
    MAB = "MAB"
    EAP = "EAP"


class PortLocking(enum.Enum):
    SWITCH_PORT = "switch_port"
    SWITCH = "switch"


class PortType(enum.Enum):
    WIRED = "Ethernet"
    WIRELESS = "Wireless-802.11"


class MatchLogic(enum.Enum):
    AND = "AND"  # Every condition must match
    OR = "OR"  # At least one condition must match


class ConditionOperator(enum.Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    CONTAINS = "in"
    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"
    REGEX = "regex"
    IN_LIST = "in_list"


class ReplyOperator(enum.Enum):
    EQUALS = "="
    SET_EQUALS = ":="


class Policy(Base, TimestampsMixin):
    __tablename__ = "policy"
    __table_args__ = (UniqueConstraint("name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    description: Mapped[Optional[str]] = mapped_column(String(255))

    # Priority: Lower number = evaluated first
    priority: Mapped[int] = mapped_column(Integer, default=100, index=True)

    port_locking: Mapped[Optional[PortLocking]] = mapped_column(
        Enum(PortLocking), nullable=True
    )

    client_type: Mapped[Optional[ClientType]] = mapped_column(
        Enum(ClientType), nullable=True
    )

    port_type: Mapped[Optional[PortType]] = mapped_column(Enum(PortType), nullable=True)

    # AND/OR logic for the attached conditions
    match_logic: Mapped[MatchLogic] = mapped_column(
        Enum(MatchLogic), default=MatchLogic.AND
    )

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    conditions: Mapped[List["PolicyCondition"]] = relationship(
        "PolicyCondition",
        back_populates="policy",
        lazy="selectin",
        cascade="all, delete-orphan",  # Deleting a rule deletes its conditions
    )

    replies: Mapped[List["PolicyReply"]] = relationship(
        "PolicyReply",
        back_populates="policy",
        lazy="selectin",
        cascade="all, delete-orphan",  # Deleting a rule deletes its replies
    )

    radpostauths: Mapped[list["RadPostAuth"]] = relationship(
        primaryjoin=id == foreign(RadPostAuth.matched_policy_id),
        foreign_keys="[RadPostAuth.matched_policy_id]",
        cascade="all, delete-orphan",
    )


class PolicyCondition(Base):
    __tablename__ = "policy_condition"
    __table_args__ = (
        CheckConstraint(
            "(value_ref IS NOT NULL AND group_id IS NULL) OR (value_ref IS NULL AND group_id IS NOT NULL)",
            name="check_exclusive_reference",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policy.id"), index=True)

    attribute: Mapped[str] = mapped_column(String(100))

    operator: Mapped[ConditionOperator] = mapped_column(Enum(ConditionOperator))

    value_ref: Mapped[Optional[str]] = mapped_column(String(255))

    policy: Mapped["Policy"] = relationship("Policy", back_populates="conditions")

    group_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("endpoint_group.id"), nullable=True
    )

    group: Mapped[Optional["EndpointGroup"]] = relationship()

    @property
    def value(self) -> str | int:
        """Returns the group_id if it exists, otherwise the string."""
        if self.group_id is not None:
            return self.group_id
        # mypy fix
        assert self.value_ref
        return self.value_ref

    @value.setter
    def value(self, v):
        """Sets the appropriate column based on the type of value passed."""
        if isinstance(v, int):
            self.group_id = v
            self.value_ref = None
        elif isinstance(v, str):
            self.value_ref = v
            self.group_id = None
        else:
            raise ValueError("Value must be a string or a group_id.")


class PolicyReply(Base):
    __tablename__ = "policy_reply"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_id: Mapped[int] = mapped_column(ForeignKey("policy.id"), index=True)

    attribute: Mapped[str] = mapped_column(String(100))

    operator: Mapped[ReplyOperator] = mapped_column(Enum(ReplyOperator))

    value: Mapped[str] = mapped_column(String(255))

    policy: Mapped["Policy"] = relationship("Policy", back_populates="replies")
