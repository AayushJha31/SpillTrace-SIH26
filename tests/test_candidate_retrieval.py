from __future__ import annotations

from data.scoring.candidate_retrieval import (
    StoredCandidate,
    get_candidates_for_spill,
)


def test_candidate_retrieval_imports_cleanly() -> None:
    assert callable(get_candidates_for_spill)

    field_names = [f.name for f in StoredCandidate.__dataclass_fields__.values()]

    assert "spill_id" in field_names
    assert "mmsi" in field_names
    assert "rank" in field_names
    assert "score" in field_names
    assert "evidence" in field_names