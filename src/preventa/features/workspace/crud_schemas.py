from typing import Literal

from pydantic import BaseModel, Field


class StudyCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    client: str = Field(min_length=2, max_length=160)
    facility: str = Field(min_length=2, max_length=160)


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

