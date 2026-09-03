from __future__ import annotations

from data.scoring.candidate_retrieval import StoredCandidate


def generate_candidate_report(
    candidates: list[StoredCandidate],
    spill_id: int,
) -> str:
    if not candidates:
        return f"No candidates recorded for spill_id={spill_id}."

    lines = [
        f"Candidate report for spill_id={spill_id}",
        "",
    ]

    for c in candidates:
        lines.append(
            f"Rank {c.rank}: MMSI {c.mmsi} — total_score={c.score.total_score:.3f}, "
            f"uncertainty={c.score.uncertainty_score:.2f}"
        )

    return "\n".join(lines)