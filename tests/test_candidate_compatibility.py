from __future__ import annotations

from data.scoring.candidate_compatibility import (
    is_candidate_persistence_allowed,
)


def test_candidate_persistence_allowed_only_when_compatible() -> None:
    assert is_candidate_persistence_allowed(compatibility_state="compatible") is True
    assert is_candidate_persistence_allowed(compatibility_state="incompatible") is False
    assert is_candidate_persistence_allowed(compatibility_state="unknown") is False
    assert is_candidate_persistence_allowed(compatibility_state="") is False