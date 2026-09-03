from __future__ import annotations

from data.scoring.candidate_scoring import CandidateScore


def validate_candidate_score(score: CandidateScore) -> list[str]:
    errors: list[str] = []

    feature_scores = [
        ("spatial_proximity_score", score.spatial_proximity_score),
        ("temporal_overlap_score", score.temporal_overlap_score),
        ("heading_compatibility_score", score.heading_compatibility_score),
        ("route_intersection_score", score.route_intersection_score),
        ("track_continuity_score", score.track_continuity_score),
        ("ais_completeness", score.ais_completeness),
    ]

    for name, value in feature_scores:
        if not isinstance(value, (int, float)):
            errors.append(f"{name} must be numeric, got {type(value).__name__}")
            continue

        if not (0.0 <= value <= 1.0):
            errors.append(f"{name} must be between 0 and 1, got {value}")

    if not isinstance(score.uncertainty_score, (int, float)):
        errors.append(
            f"uncertainty_score must be numeric, got {type(score.uncertainty_score).__name__}"
        )
    elif not (0.0 <= score.uncertainty_score <= 1.0):
        errors.append(f"uncertainty_score must be between 0 and 1, got {score.uncertainty_score}")

    if not isinstance(score.total_score, (int, float)):
        errors.append(f"total_score must be numeric, got {type(score.total_score).__name__}")
    elif not (0.0 <= score.total_score <= 1.0):
        errors.append(f"total_score must be between 0 and 1, got {score.total_score}")

    return errors