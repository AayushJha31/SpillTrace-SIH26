from __future__ import annotations

from data.scoring.candidate_docs import generate_scoring_docs


def test_generate_scoring_docs_returns_markdown_with_features_and_weights() -> None:
    docs = generate_scoring_docs()

    assert "# Candidate scoring model" in docs
    assert "Current scoring version:" in docs
    assert "v1.0" in docs
    assert "## Features" in docs
    assert "spatial_proximity_score" in docs
    assert "temporal_overlap_score" in docs
    assert "heading_compatibility_score" in docs
    assert "route_intersection_score" in docs
    assert "track_continuity_score" in docs
    assert "ais_completeness" in docs
    assert "## Uncertainty" in docs
    assert "weight=" in docs