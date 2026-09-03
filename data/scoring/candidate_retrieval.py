from __future__ import annotations

import json
from dataclasses import dataclass

import psycopg

from data.scoring.candidate_scoring import CandidateScore


DATABASE_CONNECTION = (
    "host=localhost "
    "port=5432 "
    "dbname=spilltrace "
    "user=spilltrace "
    "password=spilltrace_local_password"
)


@dataclass
class StoredCandidate:
    spill_id: int
    mmsi: int
    rank: int
    score: CandidateScore
    evidence: dict


def get_candidates_for_spill(*, spill_id: int) -> list[StoredCandidate]:
    query = """
        SELECT
            spill_id,
            mmsi,
            rank,
            total_score,
            spatial_proximity_score,
            temporal_overlap_score,
            heading_compatibility_score,
            route_intersection_score,
            track_continuity_score,
            ais_completeness,
            uncertainty_score,
            evidence_json,
            scoring_version
        FROM vessel_candidates
        WHERE spill_id = %(spill_id)s
        ORDER BY rank ASC
    """

    parameters = {"spill_id": spill_id}

    rows: list[tuple] = []

    with psycopg.connect(DATABASE_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

    candidates: list[StoredCandidate] = []

    for row in rows:
        (
            row_spill_id,
            row_mmsi,
            row_rank,
            row_total_score,
            row_spatial_proximity_score,
            row_temporal_overlap_score,
            row_heading_compatibility_score,
            row_route_intersection_score,
            row_track_continuity_score,
            row_ais_completeness,
            row_uncertainty_score,
            row_evidence_json,
            row_scoring_version,
        ) = row

        score = CandidateScore(
            total_score=row_total_score,
            spatial_proximity_score=row_spatial_proximity_score,
            temporal_overlap_score=row_temporal_overlap_score,
            heading_compatibility_score=row_heading_compatibility_score,
            route_intersection_score=row_route_intersection_score,
            track_continuity_score=row_track_continuity_score,
            ais_completeness=row_ais_completeness,
            uncertainty_score=row_uncertainty_score,
            scoring_version=row_scoring_version,
            contributions=[],
        )

        evidence = json.loads(row_evidence_json)

        candidates.append(
            StoredCandidate(
                spill_id=row_spill_id,
                mmsi=row_mmsi,
                rank=row_rank,
                score=score,
                evidence=evidence,
            )
        )

    return candidates