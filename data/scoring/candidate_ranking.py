from __future__ import annotations

from data.scoring.candidate_retrieval import StoredCandidate


def rank_candidates(
    candidates: list[StoredCandidate],
) -> list[StoredCandidate]:
    return sorted(candidates, key=lambda c: c.rank)