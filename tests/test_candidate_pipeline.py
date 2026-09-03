from __future__ import annotations

import json
from pathlib import Path

from data.scoring.candidate_audit import AUDIT_LOG_PATH
from data.scoring.candidate_pipeline import score_candidate_for_spill


def test_score_candidate_for_spill_returns_score_evidence_and_errors() -> None:
    initial_lines = 0
    if AUDIT_LOG_PATH.exists():
        initial_lines = len(AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines())

    score, evidence, errors = score_candidate_for_spill(
        spill_id=777,
        mmsi=555666777,
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
    assert evidence["mmsi"] == "555666777"
    assert errors == []

    assert AUDIT_LOG_PATH.exists()
    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= initial_lines + 1

    last_entry = json.loads(lines[-1])
    assert last_entry["action"] == "score_computed"
    assert last_entry["spill_id"] == 777
    assert last_entry["mmsi"] == 555666777
    assert last_entry["compatibility_state"] == "incompatible"