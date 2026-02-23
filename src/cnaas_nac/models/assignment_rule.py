import enum
from typing import List
from sqlalchemy import String, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampsMixin


class MatchLogic(enum.Enum):
    ALL = "AND"  # Every condition must match
    ANY = "OR"  # At least one condition must match


class Operator(enum.Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    CONTAINS = "in"
    STARTS_WITH = "startswith"
    ENDS_WITH = "endswith"
    REGEX = "regex"
    IN_LIST = "in_list"


class AssignmentRule(Base, TimestampsMixin):
    __tablename__ = "assignment_rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    # Priority: Lower number = evaluated first
    priority: Mapped[int] = mapped_column(Integer, default=100, index=True)

    # The VLAN to assign if the rule conditions evaluates to True
    target_vlan: Mapped[int] = mapped_column(Integer, nullable=False)

    # AND/OR logic for the attached conditions
    match_logic: Mapped[MatchLogic] = mapped_column(
        Enum(MatchLogic), default=MatchLogic.ALL
    )

    # Flag to re-evaluate existing users
    reevaluate_existing: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    conditions: Mapped[List["RuleCondition"]] = relationship(
        "RuleCondition",
        back_populates="rule",
        cascade="all, delete-orphan",  # Deleting a rule deletes its conditions
    )


class RuleCondition(Base):
    __tablename__ = "assignment_rule_condition"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("assignment_rule.id"))

    attribute: Mapped[str] = mapped_column(String(100))

    operator: Mapped[Operator] = mapped_column(Enum(Operator))

    target_value: Mapped[str] = mapped_column(String(255))

    rule: Mapped["AssignmentRule"] = relationship(
        "AssignmentRule", back_populates="conditions"
    )
