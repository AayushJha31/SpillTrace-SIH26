BEGIN;

ALTER TABLE vessel_candidates
    RENAME COLUMN score TO total_score;

ALTER TABLE vessel_candidates
    RENAME COLUMN track_continuity TO track_continuity_score;

ALTER TABLE vessel_candidates
    RENAME COLUMN evidence TO evidence_json;

ALTER TABLE vessel_candidates
    RENAME COLUMN uncertainty TO uncertainty_details;

ALTER TABLE vessel_candidates
    RENAME COLUMN score_components TO score_components_legacy;

ALTER TABLE vessel_candidates
    ADD COLUMN IF NOT EXISTS spatial_proximity_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS temporal_overlap_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS heading_compatibility_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS route_intersection_score DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS uncertainty_score DOUBLE PRECISION;

ALTER TABLE vessel_candidates
    ADD CONSTRAINT vessel_candidates_total_score_check
    CHECK (
        total_score IS NULL
        OR (
            total_score >= 0.0
            AND total_score <= 1.0
        )
    );

ALTER TABLE vessel_candidates
    ADD CONSTRAINT vessel_candidates_spatial_proximity_score_check
    CHECK (
        spatial_proximity_score IS NULL
        OR (
            spatial_proximity_score >= 0.0
            AND spatial_proximity_score <= 1.0
        )
    );

ALTER TABLE vessel_candidates
    ADD CONSTRAINT vessel_candidates_temporal_overlap_score_check
    CHECK (
        temporal_overlap_score IS NULL
        OR (
            temporal_overlap_score >= 0.0
            AND temporal_overlap_score <= 1.0
        )
    );

ALTER TABLE vessel_candidates
    ADD CONSTRAINT vessel_candidates_heading_compatibility_score_check
    CHECK (
        heading_compatibility_score IS NULL
        OR (
            heading_compatibility_score >= 0.0
            AND heading_compatibility_score <= 1.0
        )
    );

ALTER TABLE vessel_candidates
    ADD CONSTRAINT vessel_candidates_route_intersection_score_check
    CHECK (
        route_intersection_score IS NULL
        OR (
            route_intersection_score >= 0.0
            AND route_intersection_score <= 1.0
        )
    );

ALTER TABLE vessel_candidates
    ADD CONSTRAINT vessel_candidates_track_continuity_score_check
    CHECK (
        track_continuity_score IS NULL
        OR (
            track_continuity_score >= 0.0
            AND track_continuity_score <= 1.0
        )
    );

ALTER TABLE vessel_candidates
    ADD CONSTRAINT vessel_candidates_uncertainty_score_check
    CHECK (
        uncertainty_score IS NULL
        OR (
            uncertainty_score >= 0.0
            AND uncertainty_score <= 1.0
        )
    );

ALTER TABLE vessel_candidates
    ADD CONSTRAINT vessel_candidates_scoring_version_required_check
    CHECK (
        total_score IS NULL
        OR scoring_version IS NOT NULL
    );

DROP INDEX IF EXISTS idx_vessel_candidates_spill_rank;

CREATE INDEX IF NOT EXISTS idx_vessel_candidates_spill_rank
    ON vessel_candidates (spill_id, rank);

COMMIT;