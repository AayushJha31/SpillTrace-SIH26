from __future__ import annotations

from data.scoring.candidate_compatibility import (
    is_candidate_persistence_allowed,
)
from data.scoring.candidate_pipeline import score_candidate_for_spill
from data.scoring.candidate_scoring import CandidateScore


def prepare_candidate_for_persistence(
    *,
    spill_id: int,
    mmsi: int,
    spatial_proximity_score: float,
    temporal_overlap_score: float,
    heading_compatibility_score: float,
    route_intersection_score: float,
    track_continuity_score: float,
    ais_completeness: float,
    uncertainty_score: float,
    compatibility_state: str,
    scoring_version: str = "v1.0",
) -> tuple[CandidateScore, dict, list[str], bool]:
    score, evidence, validation_errors = score_candidate_for_spill(
        spill_id=spill_id,
        mmsi=mmsi,
        spatial_proximity_score=spatial_proximity_score,
        temporal_overlap_score=temporal_overlap_score,
        heading_compatibility_score=heading_compatibility_score,
        route_intersection_score=route_intersection_score,
        track_continuity_score=track_continuity_score,
        ais_completeness=ais_completeness,
        uncertainty_score=uncertainty_score,
        compatibility_state=compatibility_state,
        scoring_version=scoring_version,
    )

    persistence_allowed = is_candidate_persistence_allowed(
        compatibility_state=compatibility_state
    )

    return score, evidence, validation_errors, persistence_allowed