from __future__ import annotations


def is_candidate_persistence_allowed(
    *,
    compatibility_state: str,
) -> bool:
    return compatibility_state == "compatible"