from __future__ import annotations

import json

import psycopg

from data.scoring.candidate_scoring import CandidateScore


DATABASE_CONNECTION = (
    "host=localhost "
    "port=5432 "
    "dbname=spilltrace "
    "user=spilltrace "
    "password=spilltrace_local_password"
)


def persist_candidate(
    *,
    spill_id: int,
    mmsi: int,
    rank: int,
    compatibility_state: str,
    score: CandidateScore,
    evidence: dict,
) -> None:
    if compatibility_state != "compatible":
        raise ValueError(
            "Candidate persistence is blocked because the scenario "
            "compatibility state is not compatible."
        )

    if rank < 1:
        raise ValueError("Candidate rank must be at least 1.")

    insert_sql = """
        INSERT INTO vessel_candidates (
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
        )
        VALUES (
            %(spill_id)s,
            %(mmsi)s,
            %(rank)s,
            %(total_score)s,
            %(spatial_proximity_score)s,
            %(temporal_overlap_score)s,
            %(heading_compatibility_score)s,
            %(route_intersection_score)s,
            %(track_continuity_score)s,
            %(ais_completeness)s,
            %(uncertainty_score)s,
            %(evidence_json)s::jsonb,
            %(scoring_version)s
        )
        ON CONFLICT (spill_id, mmsi)
        DO UPDATE SET
            rank = EXCLUDED.rank,
            total_score = EXCLUDED.total_score,
            spatial_proximity_score = EXCLUDED.spatial_proximity_score,
            temporal_overlap_score = EXCLUDED.temporal_overlap_score,
            heading_compatibility_score = EXCLUDED.heading_compatibility_score,
            route_intersection_score = EXCLUDED.route_intersection_score,
            track_continuity_score = EXCLUDED.track_continuity_score,
            ais_completeness = EXCLUDED.ais_completeness,
            uncertainty_score = EXCLUDED.uncertainty_score,
            evidence_json = EXCLUDED.evidence_json,
            scoring_version = EXCLUDED.scoring_version,
            created_at = now()
    """

    parameters = {
        "spill_id": spill_id,
        "mmsi": mmsi,
        "rank": rank,
        "total_score": score.total_score,
        "spatial_proximity_score": score.spatial_proximity_score,
        "temporal_overlap_score": score.temporal_overlap_score,
        "heading_compatibility_score": score.heading_compatibility_score,
        "route_intersection_score": score.route_intersection_score,
        "track_continuity_score": score.track_continuity_score,
        "ais_completeness": score.ais_completeness,
        "uncertainty_score": score.uncertainty_score,
        "evidence_json": json.dumps(evidence),
        "scoring_version": score.scoring_version,
    }

    with psycopg.connect(DATABASE_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(insert_sql, parameters)

        connection.commit()