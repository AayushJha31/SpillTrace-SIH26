from __future__ import annotations

from dataclasses import dataclass


WEIGHTS = {
    "spatial_proximity_score": 0.30,
    "temporal_overlap_score": 0.25,
    "heading_compatibility_score": 0.15,
    "route_intersection_score": 0.15,
    "track_continuity_score": 0.10,
    "ais_completeness": 0.05,
}


@dataclass(frozen=True)
class CandidateScore:
    total_score: float
    spatial_proximity_score: float
    temporal_overlap_score: float
    heading_compatibility_score: float
    route_intersection_score: float
    track_continuity_score: float
    ais_completeness: float
    uncertainty_score: float | None
    contributions: dict[str, float]
    scoring_version: str


def validate_score(
    value: float | int,
    field_name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"{field_name} must be a numeric value between 0.0 and 1.0."
        )

    score = float(value)

    if not 0.0 <= score <= 1.0:
        raise ValueError(
            f"{field_name} must be between 0.0 and 1.0."
        )

    return score


def calculate_candidate_score(
    *,
    spatial_proximity_score: float,
    temporal_overlap_score: float,
    heading_compatibility_score: float,
    route_intersection_score: float,
    track_continuity_score: float,
    ais_completeness: float,
    uncertainty_score: float | None = None,
    scoring_version: str = "v1.0",
) -> CandidateScore:
    feature_scores = {
        "spatial_proximity_score": validate_score(
            spatial_proximity_score,
            "spatial_proximity_score",
        ),
        "temporal_overlap_score": validate_score(
            temporal_overlap_score,
            "temporal_overlap_score",
        ),
        "heading_compatibility_score": validate_score(
            heading_compatibility_score,
            "heading_compatibility_score",
        ),
        "route_intersection_score": validate_score(
            route_intersection_score,
            "route_intersection_score",
        ),
        "track_continuity_score": validate_score(
            track_continuity_score,
            "track_continuity_score",
        ),
        "ais_completeness": validate_score(
            ais_completeness,
            "ais_completeness",
        ),
    }

    validated_uncertainty = (
        None
        if uncertainty_score is None
        else validate_score(
            uncertainty_score,
            "uncertainty_score",
        )
    )

    contributions = {
        field_name: round(
            feature_scores[field_name] * weight,
            6,
        )
        for field_name, weight in WEIGHTS.items()
    }

    total_score = round(sum(contributions.values()), 6)

    return CandidateScore(
        total_score=total_score,
        spatial_proximity_score=feature_scores[
            "spatial_proximity_score"
        ],
        temporal_overlap_score=feature_scores[
            "temporal_overlap_score"
        ],
        heading_compatibility_score=feature_scores[
            "heading_compatibility_score"
        ],
        route_intersection_score=feature_scores[
            "route_intersection_score"
        ],
        track_continuity_score=feature_scores[
            "track_continuity_score"
        ],
        ais_completeness=feature_scores["ais_completeness"],
        uncertainty_score=validated_uncertainty,
        contributions=contributions,
        scoring_version=scoring_version,
    )

def build_candidate_evidence(
    *,
    mmsi: str,
    score: CandidateScore,
) -> dict:
    return {
        "summary": (
            "Highest-ranked candidate under available evidence. "
            "This is an investigative lead, not a confirmed polluter."
        ),
        "mmsi": mmsi,
        "scoring_version": score.scoring_version,
        "total_score": score.total_score,
        "feature_scores": {
            "spatial_proximity_score": (
                score.spatial_proximity_score
            ),
            "temporal_overlap_score": (
                score.temporal_overlap_score
            ),
            "heading_compatibility_score": (
                score.heading_compatibility_score
            ),
            "route_intersection_score": (
                score.route_intersection_score
            ),
            "track_continuity_score": (
                score.track_continuity_score
            ),
            "ais_completeness": score.ais_completeness,
        },
        "weighted_contributions": score.contributions,
        "uncertainty_score": score.uncertainty_score,
        "limitations": [
            "Candidate ranking is decision support only.",
            "A candidate ranking does not establish legal responsibility.",
            "Evidence quality depends on SAR, drift, AIS coverage, and compatibility validation.",
        ],
    }

def summarize_candidate_score(score: CandidateScore) -> dict:
    return {
        "scoring_version": score.scoring_version,
        "total_score": score.total_score,
        "uncertainty_score": score.uncertainty_score,
        "feature_scores": {
            "spatial_proximity_score": score.spatial_proximity_score,
            "temporal_overlap_score": score.temporal_overlap_score,
            "heading_compatibility_score": score.heading_compatibility_score,
            "route_intersection_score": score.route_intersection_score,
            "track_continuity_score": score.track_continuity_score,
            "ais_completeness": score.ais_completeness,
        },
    }