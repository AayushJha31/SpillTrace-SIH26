from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

class CandidateErrorCode(str, Enum):
    compatibility_failed = "COMPATIBILITY_FAILED"
    no_candidates = "NO_CANDIDATES"
    spill_not_found = "SPILL_NOT_FOUND"
    candidate_not_found = "CANDIDATE_NOT_FOUND"

class CompatibilityStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compatible: bool
    status: Literal["passed", "blocked"]
    temporal_overlap: bool
    geographic_overlap: bool
    crs_valid: bool
    environmental_coverage: bool
    reasons: list[str] = Field(default_factory=list)

class ScoreContributions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spatial: float = Field(ge=0, le=1)
    temporal: float = Field(ge=0, le=1)
    heading: float = Field(ge=0, le=1)
    intersection: float = Field(ge=0, le=1)
    continuity: float = Field(ge=0, le=1)
    quality: float = Field(ge=0, le=1)

class WeightedScoreContributions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spatial: float
    temporal: float
    heading: float
    intersection: float
    continuity: float
    quality: float

class AISQuality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    track_continuity: float = Field(ge=0, le=1)
    data_completeness: float = Field(ge=0, le=1)
    position_count: int = Field(ge=0)
    gap_count: int = Field(ge=0)
    source: str

class DriftEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    run_type: Literal["hindcast", "forecast"]
    mode: str
    corridor_reference: str | None = None
    uncertainty_radius_m: float | None = Field(default=None, ge=0)
    assumptions: list[str] = Field(default_factory=list)

class CandidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    mmsi: str
    vessel_name: str | None = None
    spatial_score: float = Field(ge=0, le=1)
    temporal_score: float = Field(ge=0, le=1)
    heading_score: float = Field(ge=0, le=1)
    intersection_score: float = Field(ge=0, le=1)
    continuity_score: float = Field(ge=0, le=1)
    quality_score: float = Field(ge=0, le=1)
    distance_to_origin_m: float = Field(ge=0)
    minutes_from_origin: float
    intersects_corridor: bool
    ais_quality: AISQuality
    source_reference: str
    track_reference: str | None = None

class CandidateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    mmsi: str
    vessel_name: str | None = None
    rank: int
    score: float = Field(ge=0, le=1)
    label: Literal[
        "highest-ranked candidate under available evidence",
        "candidate under available evidence",
    ]
    score_contributions: ScoreContributions
    weighted_contributions: WeightedScoreContributions
    ais_quality: AISQuality
    drift_evidence: DriftEvidence
    evidence_statements: list[str]
    source_reference: str
    track_reference: str | None = None

class CandidateRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compatibility: CompatibilityStatus
    drift_evidence: DriftEvidence
    candidates: list[CandidateInput] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=100)

class CandidateRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    spill_id: str
    status: Literal["completed", "blocked", "no_candidates"]
    compatibility: CompatibilityStatus
    candidates: list[CandidateResult]
    data_mode: str
    disclaimer: str
    created_at_utc: datetime

class CandidateDetailResponse(CandidateResult):
    spill_id: str
    run_id: str

class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str
    timestamp_utc: datetime

class ErrorResponse(BaseModel):
    error: ErrorBody