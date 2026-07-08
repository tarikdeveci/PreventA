"""OpenPHA supporting registers (review item 6).

Beyond the Node -> Deviation -> Cause -> Consequence risk tree, an OpenPHA study
carries supporting registers that a full, lossless round-trip of a real file (the
ANAGOLD study) must preserve: the review team and their session attendance,
drawings, management-of-change and SCAI records, previous/industry incidents,
checklists and the parking lot.

Each register keeps the handful of typed fields the app displays plus a ``raw``
JSON snapshot of the original OpenPHA object, so re-export is faithful even for
the many OpenPHA housekeeping fields the typed columns do not model.  They live
in their own module to keep ``hazop.py`` focused on the risk model and under the
project's file-size limit; importing this module registers them on
``Base.metadata`` for migrations.
"""

from datetime import date
from uuid import UUID

from sqlalchemy import Column, Date, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from preventa.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# --------------------------------------------------------------------------- #
# m2m attendance: which team members attended which sessions
# (OpenPHA Sessions[].Team_Member_IDs).
# --------------------------------------------------------------------------- #

session_attendance = Table(
    "session_attendance",
    Base.metadata,
    Column(
        "session_id",
        PGUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "team_member_id",
        PGUUID(as_uuid=True),
        ForeignKey("team_members.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class TeamMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "team_members"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)
    name: Mapped[str | None] = mapped_column(String(255))  # Name
    role: Mapped[str | None] = mapped_column(String(255))  # Team_Member_Role / Role
    company: Mapped[str | None] = mapped_column(String(255))  # Company
    email: Mapped[str | None] = mapped_column(String(255))  # Email
    raw: Mapped[str | None] = mapped_column(Text)  # full OpenPHA object (JSON)

    sessions: Mapped[list["Session"]] = relationship(
        secondary=session_attendance, back_populates="attendees"
    )


class Session(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sessions"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)
    session_date: Mapped[date | None] = mapped_column(Date)  # Session_Date / Date
    description: Mapped[str | None] = mapped_column(Text)  # Session_Description
    raw: Mapped[str | None] = mapped_column(Text)

    attendees: Mapped[list[TeamMember]] = relationship(
        secondary=session_attendance, back_populates="sessions"
    )


class Drawing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "drawings"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)
    number: Mapped[str | None] = mapped_column(String(255))  # Drawing_Number
    title: Mapped[str | None] = mapped_column(Text)  # Drawing_Title / Name
    raw: Mapped[str | None] = mapped_column(Text)


class ParkingLotItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "parking_lot_items"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)
    text: Mapped[str | None] = mapped_column(Text)  # Parking_Lot_Item / Description
    raw: Mapped[str | None] = mapped_column(Text)


class Moc(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "mocs"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)
    number: Mapped[str | None] = mapped_column(String(255))  # Moc_Number
    title: Mapped[str | None] = mapped_column(Text)  # Moc_Title
    status: Mapped[str | None] = mapped_column(String(64))  # Moc_Status
    raw: Mapped[str | None] = mapped_column(Text)


class Scai(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scais"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)
    tag: Mapped[str | None] = mapped_column(String(255))  # Scai_Tag / Tag
    description: Mapped[str | None] = mapped_column(Text)  # Scai_Description
    raw: Mapped[str | None] = mapped_column(Text)


class Incident(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "incidents"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)
    # "previous" (Previous_Incidents[]) or "industry" (Industry_Incidents[]).
    kind: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    raw: Mapped[str | None] = mapped_column(Text)


class Checklist(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "checklists"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("studies.id", ondelete="CASCADE"), index=True
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)
    name: Mapped[str | None] = mapped_column(Text)  # Check_List_Name / Name
    raw: Mapped[str | None] = mapped_column(Text)
