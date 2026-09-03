from __future__ import annotations

import pytest

from data.scoring.candidate_persistence import persist_candidate
from data.scoring.candidate_scoring import (
    CandidateScore,
    calculate_candidate_score,
)


def test_persist_candidate_rejected_when_compatibility_not_compatible() -> None:
    score = calculate_candidate_score(
        spatial_proximity_score=0.9,
        temporal_overlap_score=0.8,
        heading_compatibility_score=0.7,
        route_intersection_score=1.0,
        track_continuity_score=0.8,
        ais_completeness=0.9,
        uncertainty_score=0.2,
        scoring_version="v1.0",
    )

    evidence = {
        "summary": "Test evidence",
        "mmsi": "123456789",
        "total_score": score.total_score,
        "feature_scores": {},
        "weighted_contributions": [],
        "uncertainty_score": score.uncertainty_score,
        "limitations": [],
    }

    with pytest.raises(
        ValueError,
        match=(
            "Candidate persistence is blocked because the scenario "
            "compatibility state is not compatible"
        ),
    ):
        persist_candidate(
            spill_id=1,
            mmsi=123456789,
            rank=1,
            compatibility_state="incompatible",
            score=score,
            evidence=evidence,
        )