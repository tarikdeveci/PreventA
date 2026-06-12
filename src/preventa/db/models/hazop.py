from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from preventa.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StudyStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class Study(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "studies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    facility: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[StudyStatus] = mapped_column(
        Enum(StudyStatus, name="study_status"),
        default=StudyStatus.DRAFT,
        nullable=False,
    )

    nodes: Mapped[list["HazopNode"]] = relationship(
        back_populates="study",
        cascade="all, delete-orphan",
    )


class HazopNode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hazop_nodes"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("studies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    design_intent: Mapped[str] = mapped_column(Text, nullable=False)
    equipment_type: Mapped[str | None] = mapped_column(String(100), index=True)

    study: Mapped[Study] = relationship(back_populates="nodes")
    worksheet_rows: Mapped[list["HazopWorksheetRow"]] = relationship(
        back_populates="node",
        cascade="all, delete-orphan",
    )


class HazopWorksheetRow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "hazop_worksheet_rows"

    node_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hazop_nodes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    parameter: Mapped[str] = mapped_column(String(100), nullable=False)
    guideword: Mapped[str] = mapped_column(String(100), nullable=False)
    deviation: Mapped[str] = mapped_column(Text, nullable=False)
    cause: Mapped[str | None] = mapped_column(Text)
    consequence: Mapped[str | None] = mapped_column(Text)
    safeguard: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status"),
        default=ReviewStatus.DRAFT,
        nullable=False,
    )

    node: Mapped[HazopNode] = relationship(back_populates="worksheet_rows")

