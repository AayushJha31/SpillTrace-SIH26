from __future__ import annotations

from data.scoring.candidate_config import (
    FEATURE_DESCRIPTIONS,
    SCORING_VERSION,
    UNCERTAINTY_DESCRIPTION,
)


def test_candidate_config_has_required_fields() -> None:
    assert isinstance(SCORING_VERSION, str)
    assert SCORING_VERSION == "v1.0"

    assert isinstance(FEATURE_DESCRIPTIONS, dict)
    assert "spatial_proximity_score" in FEATURE_DESCRIPTIONS
    assert "temporal_overlap_score" in FEATURE_DESCRIPTIONS
    assert "heading_compatibility_score" in FEATURE_DESCRIPTIONS
    assert "route_intersection_score" in FEATURE_DESCRIPTIONS
    assert "track_continuity_score" in FEATURE_DESCRIPTIONS
    assert "ais_completeness" in FEATURE_DESCRIPTIONS

    assert isinstance(UNCERTAINTY_DESCRIPTION, str)
    assert "uncertainty" in UNCERTAINTY_DESCRIPTION.lower()