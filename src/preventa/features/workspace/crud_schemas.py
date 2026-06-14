from typing import Literal

from pydantic import BaseModel, Field


class StudyCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    client: str = Field(min_length=2, max_length=160)
    facility: str = Field(min_length=2, max_length=160)


class StudyUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    client: str | None = Field(default=None, min_length=2, max_length=160)
    facility: str | None = Field(default=None, min_length=2, max_length=160)
    status: Literal["draft", "in_review", "complete"] | None = None


class StudyItem(StudyCreate):
    id: str
    status: str
    node_count: int = 0


class NodeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=2, max_length=160)
    equipment_type: str = Field(min_length=2, max_length=120)
    design_intent: str = Field(min_length=2)


class NodeUpdate(BaseModel):
    name: str | None = None
    equipment_type: str | None = None
    design_intent: str | None = None
    state: Literal["empty", "active", "review", "complete"] | None = None


class RowCreate(BaseModel):
    guideword: str = "Yok"
    deviation: str = ""
    cause: str = ""
    consequence: str = ""
    safeguard: str = ""
    severity: int = Field(default=1, ge=1, le=5)
    likelihood: int = Field(default=1, ge=1, le=5)
    status: str = "Eksik"


class RowUpdate(BaseModel):
    guideword: str | None = None
    deviation: str | None = None
    cause: str | None = None
    consequence: str | None = None
    safeguard: str | None = None
    severity: int | None = Field(default=None, ge=1, le=5)
    likelihood: int | None = Field(default=None, ge=1, le=5)
    status: str | None = None


class LopaLayerCreate(BaseModel):
    description: str = Field(min_length=2)
    pfd: float = Field(gt=0, le=1)
    is_valid: bool = True
    note: str = ""


class LibraryEntryCreate(BaseModel):
    equipment_type: str = Field(min_length=2, max_length=120)
    guideword: str = Field(min_length=1, max_length=40)
    deviation: str = Field(min_length=2, max_length=240)
    cause: str = Field(min_length=2)
    consequence: str = Field(min_length=2)
    safeguard: str = ""
    severity: int = Field(default=3, ge=1, le=5)
    likelihood: int = Field(default=2, ge=1, le=5)
    source_ref: str = Field(default="", max_length=240)


class SourceCreate(BaseModel):
    study_id: str
    title: str = Field(min_length=2, max_length=200)
    source_type: Literal["Standard", "Historical study", "Procedure", "Drawing", "Other"]
    reference: str = Field(default="", max_length=500)
    section_count: int = Field(default=0, ge=0)


class SourceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    source_type: Literal[
        "Standard", "Historical study", "Procedure", "Drawing", "Other"
    ] | None = None
    reference: str | None = Field(default=None, max_length=500)
    section_count: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class RiskMatrixUpdate(BaseModel):
    low_max: int = Field(ge=1, le=24)
    medium_max: int = Field(ge=2, le=24)
    high_max: int = Field(ge=3, le=24)
