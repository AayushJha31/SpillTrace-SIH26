from __future__ import annotations

import json
from pathlib import Path

from data.scoring.candidate_audit import AUDIT_LOG_PATH, log_candidate_action
from data.scoring.candidate_scoring import CandidateScore


def test_log_candidate_action_writes_jsonl() -> None:
    score = CandidateScore(
        total_score=0.85,
        spatial_proximity_score=0.9,
        temporal_overlap_score=0.8,
        heading_compatibility_score=0.7,
        route_intersection_score=1.0,
        track_continuity_score=0.8,
        ais_completeness=0.9,
        uncertainty_score=0.2,
        scoring_version="v1.0",
        contributions=[],
    )

    initial_lines = 0
    if AUDIT_LOG_PATH.exists():
        initial_lines = len(AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines())

    log_candidate_action(
        action="persist_attempt",
        spill_id=999,
        mmsi=111222333,
        rank=1,
        score=score,
        compatibility_state="incompatible",
        details={"reason": "blocked_scenario"},
    )

    assert AUDIT_LOG_PATH.exists()

    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()
    assert len(lines) == initial_lines + 1

    last_entry = json.loads(lines[-1])

    assert last_entry["action"] == "persist_attempt"
    assert last_entry["spill_id"] == 999
    assert last_entry["mmsi"] == 111222333
    assert last_entry["rank"] == 1
    assert last_entry["total_score"] == 0.85
    assert last_entry["compatibility_state"] == "incompatible"
    assert last_entry["details"]["reason"] == "blocked_scenario"