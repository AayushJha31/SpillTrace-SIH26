from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from data.scoring.candidate_scoring import CandidateScore


AUDIT_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "logs" / "candidate_audit.jsonl"


def log_candidate_action(
    *,
    action: str,
    spill_id: int,
    mmsi: int,
    rank: int | None,
    score: CandidateScore,
    compatibility_state: str,
    details: dict | None = None,
) -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "spill_id": spill_id,
        "mmsi": mmsi,
        "rank": rank,
        "total_score": score.total_score,
        "compatibility_state": compatibility_state,
        "details": details or {},
    }

    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")