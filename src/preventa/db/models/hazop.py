"""PreventA HAZOP/LOPA data model, aligned 1:1 with the OpenPHA schema.

Replaces the original single flat ``HazopWorksheetRow`` with the real OpenPHA
tree so a study can be modelled — and round-tripped through ``.opha`` — without
losing structure:

    Study -> Node -> Deviation -> Cause -> Consequence
                                              |-- (m2m) Safeguard (IPL / SIL)
                                              |-- Lopa (1:1 LOPA layer)
                                              |-- Recommendation (PHA + LOPA)

Every column carries a comment naming the OpenPHA key it maps to, so an
``.opha`` import/export can be written mechanically.  Supporting registers
(team, sessions, drawings, MOC, SCAI, incidents, checklists, parking lot) are
left as a TODO at the end so the core risk model lands first.

Based on the employer's ``openpha-mapping/models_openpha.py`` review artifact,
adapted to PreventA's conventions and integrated with the existing RAG models
(``rag_suggestions`` now references ``consequences`` instead of the dropped
``hazop_worksheet_rows``).
"""

from datetime import date
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from preventa.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


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


class AnalysisMode(StrEnum):
    """OpenPHA ``Settings.Analysis_Mode``."""

    HAZOP = "hazop"
    WHAT_IF = "what_if"
    CHECKLIST = "checklist"


class RecommendationKind(StrEnum):
    PHA = "pha"
    LOPA = "lopa"


# --------------------------------------------------------------------------- #
# m2m link: a consequence is protected by many safeguards; a safeguard may
# protect many consequences (OpenPHA ``Consequence.Safeguard_IDs``).
# --------------------------------------------------------------------------- #

consequence_safeguard = Table(
    "consequence_safeguard",
    Base.metadata,
    Column(
        "consequence_id",
        PGUUID(as_uuid=True),
        ForeignKey("consequences.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "safeguard_id",
        PGUUID(as_uuid=True),
        ForeignKey("safeguards.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# --------------------------------------------------------------------------- #
# Study (OpenPHA Overview + Settings)
# --------------------------------------------------------------------------- #


class Study(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "studies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)  # Overview.Study_Name
    status: Mapped[StudyStatus] = mapped_column(
        Enum(StudyStatus, name="study_status"),
        default=StudyStatus.DRAFT,
        nullable=False,
    )

    # --- Overview ---------------------------------------------------------- #
    coordinator: Mapped[str | None] = mapped_column(String(255))  # Study_Coordinator
    coordinator_contact: Mapped[str | None] = mapped_column(String(255))
    pha_type: Mapped[str | None] = mapped_column(String(100))  # Pha_Type
    facility: Mapped[str | None] = mapped_column(String(255))  # Facility
    facility_location: Mapped[str | None] = mapped_column(String(255))
    facility_owner: Mapped[str | None] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))  # Overview_Company
    site: Mapped[str | None] = mapped_column(String(255))
    plant: Mapped[str | None] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(255))
    report_number: Mapped[str | None] = mapped_column(String(100))
    project_number: Mapped[str | None] = mapped_column(String(100))
    project_description: Mapped[str | None] = mapped_column(Text)
    general_notes: Mapped[str | None] = mapped_column(Text)
    revalidation_due_date: Mapped[date | None] = mapped_column(Date)

    # --- Settings (the few that drive logic; keep the rest in a JSON blob) -- #
    analysis_mode: Mapped[AnalysisMode] = mapped_column(
        Enum(AnalysisMode, name="analysis_mode"),
        default=AnalysisMode.HAZOP,
        nullable=False,
    )
    lopa_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # Settings.Lopa_Mode

    nodes: Mapped[list["Node"]] = relationship(
        back_populates="study", cascade="all, delete-orphan"
    )
    safeguards: Mapped[list["Safeguard"]] = relationship(
        back_populates="study", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="study", cascade="all, delete-orphan"
    )
    risk_matrix: Mapped["RiskMatrix | None"] = relationship(
        back_populates="study", cascade="all, delete-orphan", uselist=False
    )


# --------------------------------------------------------------------------- #
# Node (OpenPHA Nodes[])
# --------------------------------------------------------------------------- #


class Node(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "nodes"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("studies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)  # OpenPHA Nodes[].ID
    description: Mapped[str] = mapped_column(Text, nullable=False)  # Node_Description
    intention: Mapped[str | None] = mapped_column(Text)  # Intention
    boundary: Mapped[str | None] = mapped_column(Text)  # Boundary
    design_conditions: Mapped[str | None] = mapped_column(Text)
    operating_conditions: Mapped[str | None] = mapped_column(Text)
    hazardous_materials: Mapped[str | None] = mapped_column(Text)
    equipment_tags: Mapped[str | None] = mapped_column(Text)  # Equipment_Tags
    location: Mapped[str | None] = mapped_column(String(255))
    comments: Mapped[str | None] = mapped_column(Text)  # Node_Comments

    study: Mapped[Study] = relationship(back_populates="nodes")
    deviations: Mapped[list["Deviation"]] = relationship(
        back_populates="node", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# Deviation (OpenPHA Nodes[].Deviations[])
# --------------------------------------------------------------------------- #


class Deviation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deviations"

    node_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)  # OpenPHA Deviations[].ID
    parameter: Mapped[str] = mapped_column(String(100), nullable=False)  # Parameter
    guideword: Mapped[str] = mapped_column(String(100), nullable=False)  # Guide_Word
    deviation: Mapped[str] = mapped_column(Text, nullable=False)  # Deviation
    design_intent: Mapped[str | None] = mapped_column(Text)  # Design_Intent
    comments: Mapped[str | None] = mapped_column(Text)  # Deviation_Comments

    node: Mapped[Node] = relationship(back_populates="deviations")
    causes: Mapped[list["Cause"]] = relationship(
        back_populates="deviation", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# Cause (OpenPHA ...Deviations[].Causes[])
# --------------------------------------------------------------------------- #


class Cause(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "causes"

    deviation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("deviations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)  # OpenPHA Causes[].ID
    cause: Mapped[str] = mapped_column(Text, nullable=False)  # Cause
    cause_type: Mapped[str | None] = mapped_column(String(100))  # Cause_Type
    enabling_events: Mapped[str | None] = mapped_column(Text)  # Enabling_Events
    frequency: Mapped[float | None] = mapped_column(Float)  # Frequency (per year)

    deviation: Mapped[Deviation] = relationship(back_populates="causes")
    consequences: Mapped[list["Consequence"]] = relationship(
        back_populates="cause", cascade="all, delete-orphan"
    )


# --------------------------------------------------------------------------- #
# Consequence (OpenPHA ...Causes[].Consequences[]) -- the HAZOP scenario.
#
# Risk is tracked in THREE states, exactly as OpenPHA does:
#   *_before_safeguards    -> inherent / unmitigated
#   *_current              -> with existing safeguards
#   *_after_recommendations -> residual after recs are implemented
# --------------------------------------------------------------------------- #


class Consequence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "consequences"

    cause_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("causes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)  # OpenPHA Consequences[].ID
    consequence: Mapped[str] = mapped_column(Text, nullable=False)  # Consequence
    consequence_type_id: Mapped[str | None] = mapped_column(String(64))

    # Three-state risk (FKs into the study's RiskMatrix axes; ints keep it simple)
    severity_before: Mapped[int | None] = mapped_column(Integer)  # ..._Before_Safeguards
    likelihood_before: Mapped[int | None] = mapped_column(Integer)
    risk_rank_before: Mapped[str | None] = mapped_column(String(32))

    severity_current: Mapped[int | None] = mapped_column(Integer)  # Consequence_Severity_ID
    likelihood_current: Mapped[int | None] = mapped_column(Integer)  # Likelihood_ID
    risk_rank_current: Mapped[str | None] = mapped_column(String(32))  # Risk_Rank_ID

    severity_after_recs: Mapped[int | None] = mapped_column(Integer)
    likelihood_after_recs: Mapped[int | None] = mapped_column(Integer)
    risk_rank_after_recs: Mapped[str | None] = mapped_column(String(32))

    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status"),
        default=ReviewStatus.DRAFT,
        nullable=False,
    )

    cause: Mapped[Cause] = relationship(back_populates="consequences")
    safeguards: Mapped[list["Safeguard"]] = relationship(
        secondary=consequence_safeguard, back_populates="consequences"
    )
    lopa: Mapped["Lopa | None"] = relationship(
        back_populates="consequence", cascade="all, delete-orphan", uselist=False
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="consequence"
    )


# --------------------------------------------------------------------------- #
# Safeguard (OpenPHA Safeguards[]) -- structured IPL / SIL object.
# --------------------------------------------------------------------------- #


class Safeguard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "safeguards"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("studies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    opha_id: Mapped[str | None] = mapped_column(String(64), index=True)  # OpenPHA Safeguards[].ID
    description: Mapped[str] = mapped_column(Text, nullable=False)  # Safeguard
    safeguard_type: Mapped[str | None] = mapped_column(String(100))  # Safeguard_Type
    category: Mapped[str | None] = mapped_column(String(100))  # Safeguard_Category
    ipl_tag: Mapped[str | None] = mapped_column(String(100))  # Ipl_Tag

    # IPL qualification (the four LOPA independence tests)
    is_safeguard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    independent: Mapped[bool | None] = mapped_column(Boolean)  # Safeguard_Independent
    auditable: Mapped[bool | None] = mapped_column(Boolean)  # Safeguard_Auditable
    effective: Mapped[bool | None] = mapped_column(Boolean)  # Safeguard_Effective
    is_ipl: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Is_Ipl

    # SIL / reliability
    pfd: Mapped[float | None] = mapped_column(Float)  # Pfd
    safety_critical: Mapped[bool | None] = mapped_column(Boolean)  # Safety_Critical
    selected_sil: Mapped[int | None] = mapped_column(Integer)  # Selected_Sil
    required_response_time: Mapped[str | None] = mapped_column(String(64))
    test_interval: Mapped[str | None] = mapped_column(String(64))
    comments: Mapped[str | None] = mapped_column(Text)

    study: Mapped[Study] = relationship(back_populates="safeguards")
    consequences: Mapped[list[Consequence]] = relationship(
        secondary=consequence_safeguard, back_populates="safeguards"
    )


# --------------------------------------------------------------------------- #
# Lopa (the LOPA layer carried on each OpenPHA Consequence) -- 1:1 with
# Consequence so non-LOPA scenarios simply have no row.
# --------------------------------------------------------------------------- #


class Lopa(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lopa"

    consequence_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consequences.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    lopa_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Lopa_Required
    recommended_sil: Mapped[int | None] = mapped_column(Integer)  # Recommended_Sil
    tmel: Mapped[float | None] = mapped_column(Float)  # Tmel (target mitigated event likelihood)
    mel: Mapped[float | None] = mapped_column(Float)  # Mel (mitigated event likelihood)
    lopa_ratio: Mapped[float | None] = mapped_column(Float)  # Lopa_Ratio
    rrf: Mapped[float | None] = mapped_column(Float)  # Rrf (risk reduction factor)
    alarp_required: Mapped[bool | None] = mapped_column(Boolean)  # Alarp_Required
    # Conditional_Modifiers -> own child rows if you need probabilities itemised
    conditional_modifiers: Mapped[str | None] = mapped_column(Text)

    consequence: Mapped[Consequence] = relationship(back_populates="lopa")


# --------------------------------------------------------------------------- #
# Recommendation (OpenPHA Pha_Recommendations[] + Lopa_Recommendations[])
# --------------------------------------------------------------------------- #


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("studies.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Recommendations attach to a scenario in OpenPHA via Consequence.*_IDs
    consequence_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("consequences.id", ondelete="SET NULL"),
        index=True,
    )
    opha_id: Mapped[str | None] = mapped_column(
        String(64), index=True
    )  # OpenPHA Pha_/Lopa_Recommendations[].ID
    kind: Mapped[RecommendationKind] = mapped_column(
        Enum(RecommendationKind, name="recommendation_kind"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str | None] = mapped_column(String(32))
    responsible_party: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(64))
    due_date: Mapped[date | None] = mapped_column(Date)
    pfd: Mapped[float | None] = mapped_column(Float)  # Lopa_Recommendation_Pfd
    comments: Mapped[str | None] = mapped_column(Text)

    study: Mapped[Study] = relationship(back_populates="recommendations")
    consequence: Mapped[Consequence | None] = relationship(
        back_populates="recommendations"
    )


# --------------------------------------------------------------------------- #
# Risk matrix (OpenPHA Risk_Criteria) -- store the axes/cells as JSON to stay
# configurable; promote to real tables only if you need to query individual
# cells.  Postgres JSONB is ideal here but Text keeps it dialect-agnostic.
# --------------------------------------------------------------------------- #


class RiskMatrix(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "risk_matrices"

    study_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("studies.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    likelihoods: Mapped[str | None] = mapped_column(Text)  # JSON: Risk_Criteria.Likelihoods
    severities: Mapped[str | None] = mapped_column(Text)  # JSON: Severities
    intersections: Mapped[str | None] = mapped_column(Text)  # JSON: Intersections (cells)
    risk_rankings: Mapped[str | None] = mapped_column(Text)  # JSON: Risk_Rankings
    alarp_categories: Mapped[str | None] = mapped_column(Text)  # JSON: Alarp_Analysis_Categories

    study: Mapped[Study] = relationship(back_populates="risk_matrix")


# --------------------------------------------------------------------------- #
# Supporting registers -- model the ones the workflow needs next.
#   TeamMember      OpenPHA Team_Members[]
#   Session         OpenPHA Sessions[] (+ Team_Members_Sessions attendance m2m)
#   Drawing         OpenPHA Drawings[]
#   ParkingLotItem  OpenPHA Parking_Lot[]
#   Moc             OpenPHA Mocs[]
#   Scai            OpenPHA Scais[] (SCAI / SIF)
#   Incident        OpenPHA Previous_Incidents[] + Industry_Incidents[]
#   Checklist       OpenPHA Check_Lists[] + Check_List_Recommendations[]
# Left as a TODO so the core risk model lands first.
# --------------------------------------------------------------------------- #
