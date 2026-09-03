from __future__ import annotations

from data.scoring.candidate_entry import prepare_candidate_for_persistence


def test_prepare_candidate_for_persistence_returns_expected_tuple() -> None:
    score, evidence, errors, persistence_allowed = prepare_candidate_for_persistence(
        spill_id=888,
        mmsi=444555666,
        spatial_proximity_score=0.9,
        temporal_overlap_score=0.8,
        heading_compatibility_score=0.7,
        route_intersection_score=1.0,
        track_continuity_score=0.8,
        ais_completeness=0.9,
        uncertainty_score=0.2,
        compatibility_state="incompatible",
        scoring_version="v1.0",
    )

    assert score.total_score > 0
    assert evidence["mmsi"] == "444555666"
    assert errors == []
    assert persistence_allowed is False


def test_prepare_candidate_for_persistence_allows_when_compatible() -> None:
    _, _, _, persistence_allowed = prepare_candidate_for_persistence(
        spill_id=889,
        mmsi=444555667,
        spatial_proximity_score=0.9,
        temporal_overlap_score=0.8,
        heading_compatibility_score=0.7,
        route_intersection_score=1.0,
        track_continuity_score=0.8,
        ais_completeness=0.9,
        uncertainty_score=0.2,
        compatibility_state="compatible",
        scoring_version="v1.0",
    )

    assert persistence_allowed is True