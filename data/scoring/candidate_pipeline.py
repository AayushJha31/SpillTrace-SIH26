from __future__ import annotations

from data.scoring.candidate_audit import log_candidate_action
from data.scoring.candidate_compatibility import (
    is_candidate_persistence_allowed,
)
from data.scoring.candidate_scoring import (
    CandidateScore,
    build_candidate_evidence,
    calculate_candidate_score,
)
from data.scoring.candidate_validation import validate_candidate_score


def score_candidate_for_spill(
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
) -> tuple[CandidateScore, dict, list[str]]:
    score = calculate_candidate_score(
        spatial_proximity_score=spatial_proximity_score,
        temporal_overlap_score=temporal_overlap_score,
        heading_compatibility_score=heading_compatibility_score,
        route_intersection_score=route_intersection_score,
        track_continuity_score=track_continuity_score,
        ais_completeness=ais_completeness,
        uncertainty_score=uncertainty_score,
        scoring_version=scoring_version,
    )

    validation_errors = validate_candidate_score(score)

    evidence = build_candidate_evidence(
        mmsi=str(mmsi),
        score=score,
    )

    log_candidate_action(
        action="score_computed",
        spill_id=spill_id,
        mmsi=mmsi,
        rank=None,
        score=score,
        compatibility_state=compatibility_state,
        details={
            "validation_errors": validation_errors,
            "persistence_allowed": is_candidate_persistence_allowed(
                compatibility_state=compatibility_state
            ),
        },
    )

    return score, evidence, validation_errors