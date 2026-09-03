from __future__ import annotations

from data.scoring.candidate_scoring import CandidateScore
from data.scoring.candidate_validation import validate_candidate_score


def test_validate_candidate_score_accepts_valid_score() -> None:
    score = CandidateScore(
        total_score=0.85,
        spatial_proximity_score=0.9,
        temporal_overlap_score=0.8,
        heading_compatibility_score=0.7,
        route_intersection_score=1.0,
        track_continuity_score=0.8,
        ais_completeness=0.9,
        uncertainty_score=0.2,
        scoring_version="v1.0",
        contributions=[],
    )

    errors = validate_candidate_score(score)

    assert errors == []


def test_validate_candidate_score_rejects_out_of_range_features() -> None:
    score = CandidateScore(
        total_score=1.5,
        spatial_proximity_score=1.2,
        temporal_overlap_score=0.8,
        heading_compatibility_score=0.7,
        route_intersection_score=1.0,
        track_continuity_score=0.8,
        ais_completeness=0.9,
        uncertainty_score=1.5,
        scoring_version="v1.0",
        contributions=[],
    )

    errors = validate_candidate_score(score)

    assert any("spatial_proximity_score" in e for e in errors)
    assert any("total_score" in e for e in errors)
    assert any("uncertainty_score" in e for e in errors)