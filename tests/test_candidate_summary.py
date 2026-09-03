from __future__ import annotations

from data.scoring.candidate_scoring import (
    CandidateScore,
    summarize_candidate_score,
)


def test_summarize_candidate_score_returns_expected_structure() -> None:
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

    summary = summarize_candidate_score(score)

    assert summary["scoring_version"] == "v1.0"
    assert summary["total_score"] == 0.85
    assert summary["uncertainty_score"] == 0.2
    assert summary["feature_scores"]["spatial_proximity_score"] == 0.9
    assert summary["feature_scores"]["route_intersection_score"] == 1.0