from __future__ import annotations

from data.scoring.candidate_config import SCORING_VERSION
from data.scoring.candidate_scoring import (
    CandidateScore,
    build_candidate_evidence,
    calculate_candidate_score,
    summarize_candidate_score,
)
from data.scoring.candidate_validation import validate_candidate_score


def check_candidate_scoring_health() -> dict:
    try:
        score = calculate_candidate_score(
            spatial_proximity_score=0.9,
            temporal_overlap_score=0.8,
            heading_compatibility_score=0.7,
            route_intersection_score=1.0,
            track_continuity_score=0.8,
            ais_completeness=0.9,
            uncertainty_score=0.2,
            scoring_version=SCORING_VERSION,
        )

        errors = validate_candidate_score(score)
        if errors:
            return {"status": "unhealthy", "errors": errors}

        evidence = build_candidate_evidence(mmsi="999888777", score=score)
        summary = summarize_candidate_score(score)

        if not isinstance(evidence, dict) or not isinstance(summary, dict):
            return {
                "status": "unhealthy",
                "errors": ["evidence or summary is not a dict"],
            }

        return {"status": "healthy", "scoring_version": SCORING_VERSION}

    except Exception as e:
        return {"status": "unhealthy", "errors": [str(e)]}