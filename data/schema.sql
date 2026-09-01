BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS spill_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    detected_at TIMESTAMPTZ NOT NULL,

    region_name TEXT,

    status TEXT NOT NULL DEFAULT 'detected',

    source TEXT NOT NULL,

    model_version TEXT,

    confidence DOUBLE PRECISION,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT spill_events_status_check
        CHECK (
            status IN (
                'detected',
                'processing',
                'completed',
                'failed',
                'reviewed'
            )
        ),

    CONSTRAINT spill_events_confidence_check
        CHECK (
            confidence IS NULL
            OR (
                confidence >= 0.0
                AND confidence <= 1.0
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_spill_events_detected_at
    ON spill_events (detected_at);

CREATE INDEX IF NOT EXISTS idx_spill_events_status
    ON spill_events (status);

CREATE TABLE IF NOT EXISTS spill_images (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    spill_id BIGINT NOT NULL,

    storage_uri TEXT NOT NULL,

    original_filename TEXT,

    acquisition_time TIMESTAMPTZ,

    crs_epsg INTEGER,

    width INTEGER,

    height INTEGER,

    band_count INTEGER,

    bounds geometry(Polygon, 4326),

    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT spill_images_spill_fk
        FOREIGN KEY (spill_id)
        REFERENCES spill_events (id)
        ON DELETE CASCADE,

    CONSTRAINT spill_images_width_check
        CHECK (
            width IS NULL
            OR width > 0
        ),

    CONSTRAINT spill_images_height_check
        CHECK (
            height IS NULL
            OR height > 0
        ),

    CONSTRAINT spill_images_band_count_check
        CHECK (
            band_count IS NULL
            OR band_count > 0
        )
);

CREATE INDEX IF NOT EXISTS idx_spill_images_spill_id
    ON spill_images (spill_id);

CREATE INDEX IF NOT EXISTS idx_spill_images_acquisition_time
    ON spill_images (acquisition_time);

CREATE INDEX IF NOT EXISTS idx_spill_images_bounds_gist
    ON spill_images
    USING GIST (bounds);

CREATE TABLE IF NOT EXISTS ais_positions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    mmsi BIGINT NOT NULL,

    observed_at TIMESTAMPTZ NOT NULL,

    latitude DOUBLE PRECISION NOT NULL,

    longitude DOUBLE PRECISION NOT NULL,

    position geometry(Point, 4326) NOT NULL,

    sog_knots DOUBLE PRECISION,

    cog_degrees DOUBLE PRECISION,

    heading_degrees DOUBLE PRECISION,

    vessel_type INTEGER,

    source_file TEXT NOT NULL,

    source_row_number BIGINT,

    quality_flags JSONB NOT NULL DEFAULT '{}'::jsonb,

    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ais_positions_mmsi_check
        CHECK (
            mmsi BETWEEN 100000000 AND 999999999
        ),

    CONSTRAINT ais_positions_latitude_check
        CHECK (
            latitude BETWEEN -90.0 AND 90.0
        ),

    CONSTRAINT ais_positions_longitude_check
        CHECK (
            longitude BETWEEN -180.0 AND 180.0
        ),

    CONSTRAINT ais_positions_sog_check
        CHECK (
            sog_knots IS NULL
            OR sog_knots >= 0.0
        ),

    CONSTRAINT ais_positions_cog_check
        CHECK (
            cog_degrees IS NULL
            OR (
                cog_degrees >= 0.0
                AND cog_degrees < 360.0
            )
        ),

    CONSTRAINT ais_positions_heading_check
        CHECK (
            heading_degrees IS NULL
            OR (
                heading_degrees >= 0.0
                AND heading_degrees < 360.0
            )
        ),

    CONSTRAINT ais_positions_unique_observation
        UNIQUE (
            mmsi,
            observed_at,
            latitude,
            longitude
        )
);

CREATE INDEX IF NOT EXISTS idx_ais_positions_position_gist
    ON ais_positions
    USING GIST (position);

CREATE INDEX IF NOT EXISTS idx_ais_positions_mmsi_observed_at
    ON ais_positions (mmsi, observed_at);

CREATE INDEX IF NOT EXISTS idx_ais_positions_observed_at
    ON ais_positions (observed_at);

CREATE INDEX IF NOT EXISTS idx_ais_positions_quality_flags_gin
    ON ais_positions
    USING GIN (quality_flags);

CREATE TABLE IF NOT EXISTS vessel_candidates (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    spill_id BIGINT NOT NULL,

    mmsi BIGINT NOT NULL,

    rank INTEGER,

    score DOUBLE PRECISION,

    score_components JSONB NOT NULL DEFAULT '{}'::jsonb,

    ais_completeness DOUBLE PRECISION,

    track_continuity DOUBLE PRECISION,

    uncertainty JSONB NOT NULL DEFAULT '{}'::jsonb,

    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,

    scoring_version TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT vessel_candidates_spill_fk
        FOREIGN KEY (spill_id)
        REFERENCES spill_events (id)
        ON DELETE CASCADE,

    CONSTRAINT vessel_candidates_mmsi_check
        CHECK (
            mmsi BETWEEN 100000000 AND 999999999
        ),

    CONSTRAINT vessel_candidates_rank_check
        CHECK (
            rank IS NULL
            OR rank > 0
        ),

    CONSTRAINT vessel_candidates_score_check
        CHECK (
            score IS NULL
            OR score >= 0.0
        ),

    CONSTRAINT vessel_candidates_ais_completeness_check
        CHECK (
            ais_completeness IS NULL
            OR (
                ais_completeness >= 0.0
                AND ais_completeness <= 1.0
            )
        ),

    CONSTRAINT vessel_candidates_track_continuity_check
        CHECK (
            track_continuity IS NULL
            OR (
                track_continuity >= 0.0
                AND track_continuity <= 1.0
            )
        ),

    CONSTRAINT vessel_candidates_spill_mmsi_unique
        UNIQUE (
            spill_id,
            mmsi
        )
);

CREATE INDEX IF NOT EXISTS idx_vessel_candidates_spill_rank
    ON vessel_candidates (spill_id, rank);

CREATE INDEX IF NOT EXISTS idx_vessel_candidates_mmsi
    ON vessel_candidates (mmsi);

    
COMMIT;