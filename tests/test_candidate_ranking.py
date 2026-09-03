from __future__ import annotations

from data.scoring.candidate_ranking import rank_candidates
from data.scoring.candidate_retrieval import StoredCandidate
from data.scoring.candidate_scoring import CandidateScore


def test_rank_candidates_sorts_by_rank() -> None:
    base_score = CandidateScore(
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

    candidates = [
        StoredCandidate(
            spill_id=1,
            mmsi=300,
            rank=3,
            score=base_score,
            evidence={},
        ),
        StoredCandidate(
            spill_id=1,
            mmsi=100,
            rank=1,
            score=base_score,
            evidence={},
        ),
        StoredCandidate(
            spill_id=1,
            mmsi=200,
            rank=2,
            score=base_score,
            evidence={},
        ),
    ]

    ranked = rank_candidates(candidates)

    assert [c.rank for c in ranked] == [1, 2, 3]
    assert [c.mmsi for c in ranked] == [100, 200, 300]