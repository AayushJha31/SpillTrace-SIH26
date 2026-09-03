import pytest

from data.scoring.candidate_scoring import (
    WEIGHTS,
    build_candidate_evidence,
    calculate_candidate_score,
)


def test_weights_sum_to_one() -> None:
    assert sum(WEIGHTS.values()) == 1.0


def test_candidate_score_has_expected_weighted_total() -> None:
    result = calculate_candidate_score(
        spatial_proximity_score=1.0,
        temporal_overlap_score=0.8,
        heading_compatibility_score=0.6,
        route_intersection_score=0.4,
        track_continuity_score=0.2,
        ais_completeness=1.0,
        uncertainty_score=0.7,
        scoring_version="v1.0",
    )

    assert result.total_score == 0.72
    assert result.contributions == {
        "spatial_proximity_score": 0.3,
        "temporal_overlap_score": 0.2,
        "heading_compatibility_score": 0.09,
        "route_intersection_score": 0.06,
        "track_continuity_score": 0.02,
        "ais_completeness": 0.05,
    }
    assert result.uncertainty_score == 0.7
    assert result.scoring_version == "v1.0"


def test_close_but_late_candidate_scores_lower_than_timely_candidate() -> None:
    close_but_late = calculate_candidate_score(
        spatial_proximity_score=1.0,
        temporal_overlap_score=0.0,
        heading_compatibility_score=0.5,
        route_intersection_score=0.5,
        track_continuity_score=1.0,
        ais_completeness=1.0,
    )

    timely_candidate = calculate_candidate_score(
        spatial_proximity_score=0.7,
        temporal_overlap_score=1.0,
        heading_compatibility_score=0.5,
        route_intersection_score=0.5,
        track_continuity_score=1.0,
        ais_completeness=1.0,
    )

    assert timely_candidate.total_score > close_but_late.total_score


def test_corridor_intersection_increases_candidate_score() -> None:
    no_intersection = calculate_candidate_score(
        spatial_proximity_score=0.7,
        temporal_overlap_score=0.8,
        heading_compatibility_score=0.6,
        route_intersection_score=0.0,
        track_continuity_score=0.9,
        ais_completeness=0.9,
    )

    corridor_intersection = calculate_candidate_score(
        spatial_proximity_score=0.7,
        temporal_overlap_score=0.8,
        heading_compatibility_score=0.6,
        route_intersection_score=1.0,
        track_continuity_score=0.9,
        ais_completeness=0.9,
    )

    assert (
        corridor_intersection.total_score
        > no_intersection.total_score
    )
    assert (
    corridor_intersection.total_score
    - no_intersection.total_score
    ) == pytest.approx(0.15)


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("spatial_proximity_score", -0.01),
        ("temporal_overlap_score", 1.01),
        ("heading_compatibility_score", "not-a-number"),
        ("route_intersection_score", True),
        ("track_continuity_score", None),
        ("ais_completeness", 2.0),
        ("uncertainty_score", -1.0),
    ],
)
def test_invalid_scores_are_rejected(
    field_name: str,
    invalid_value,
) -> None:
    values = {
        "spatial_proximity_score": 0.5,
        "temporal_overlap_score": 0.5,
        "heading_compatibility_score": 0.5,
        "route_intersection_score": 0.5,
        "track_continuity_score": 0.5,
        "ais_completeness": 0.5,
        "uncertainty_score": 0.5,
    }

    values[field_name] = invalid_value

    with pytest.raises((TypeError, ValueError)):
        calculate_candidate_score(**values)

def test_candidate_evidence_uses_safe_investigative_language() -> None:
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

    evidence = build_candidate_evidence(
        mmsi="987654321",
        score=score,
    )

    assert evidence["mmsi"] == "987654321"
    assert evidence["total_score"] == score.total_score
    assert evidence["feature_scores"][
        "route_intersection_score"
    ] == 1.0
    assert evidence["weighted_contributions"] == score.contributions
    assert evidence["uncertainty_score"] == 0.2
    assert "not a confirmed polluter" in evidence["summary"].lower()
    assert "investigative lead" in evidence["summary"].lower()