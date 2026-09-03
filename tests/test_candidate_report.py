from __future__ import annotations

from data.scoring.candidate_ranking import rank_candidates
from data.scoring.candidate_report import generate_candidate_report
from data.scoring.candidate_retrieval import StoredCandidate
from data.scoring.candidate_scoring import CandidateScore


def test_generate_candidate_report_formats_ranked_candidates() -> None:
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

    report = generate_candidate_report(candidates=ranked, spill_id=1)

    assert "spill_id=1" in report
    assert "Rank 1: MMSI 100" in report
    assert "Rank 2: MMSI 200" in report
    assert "Rank 3: MMSI 300" in report
    assert "total_score=0.850" in report
    assert "uncertainty=0.20" in report


def test_generate_candidate_report_handles_empty_list() -> None:
    report = generate_candidate_report(candidates=[], spill_id=999)
    assert report == "No candidates recorded for spill_id=999."