from __future__ import annotations

import json
from pathlib import Path

from data.scoring.candidate_audit import AUDIT_LOG_PATH
from data.scoring.candidate_entry import prepare_candidate_for_persistence
from data.scoring.candidate_persistence import persist_candidate
from data.scoring.candidate_scoring import build_candidate_evidence


def test_candidate_flow_blocked_for_incompatible_scenario() -> None:
    initial_lines = 0
    if AUDIT_LOG_PATH.exists():
        initial_lines = len(AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines())

    score, evidence, errors, persistence_allowed = prepare_candidate_for_persistence(
        spill_id=999,
        mmsi=111222333,
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

    assert errors == []
    assert persistence_allowed is False

    evidence_for_db = build_candidate_evidence(mmsi="111222333", score=score)

    try:
        persist_candidate(
            spill_id=999,
            mmsi=111222333,
            rank=1,
            compatibility_state="incompatible",
            score=score,
            evidence=evidence_for_db,
        )
        assert False, "Expected ValueError for incompatible scenario"
    except ValueError as e:
        assert "blocked" in str(e).lower()

    assert AUDIT_LOG_PATH.exists()
    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= initial_lines + 1

    last_entry = json.loads(lines[-1])
    assert last_entry["action"] == "score_computed"
    assert last_entry["spill_id"] == 999
    assert last_entry["mmsi"] == 111222333