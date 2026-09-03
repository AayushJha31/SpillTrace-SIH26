BEGIN;

CREATE TABLE IF NOT EXISTS vessel_tracks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    spill_id BIGINT NOT NULL,

    mmsi BIGINT NOT NULL,

    track_start_time TIMESTAMPTZ NOT NULL,

    track_end_time TIMESTAMPTZ NOT NULL,

    track_geometry geometry(LineString, 4326) NOT NULL,

    position_count INTEGER NOT NULL,

    ais_completeness DOUBLE PRECISION,

    track_continuity DOUBLE PRECISION,

    gap_statistics JSONB NOT NULL DEFAULT '{}'::jsonb,

    source_file TEXT NOT NULL,

    source_provenance JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT vessel_tracks_spill_fk
        FOREIGN KEY (spill_id)
        REFERENCES spill_events (id)
        ON DELETE CASCADE,

    CONSTRAINT vessel_tracks_mmsi_check
        CHECK (
            mmsi BETWEEN 100000000 AND 999999999
        ),

    CONSTRAINT vessel_tracks_time_order_check
        CHECK (
            track_end_time >= track_start_time
        ),

    CONSTRAINT vessel_tracks_position_count_check
        CHECK (
            position_count >= 2
        ),

    CONSTRAINT vessel_tracks_ais_completeness_check
        CHECK (
            ais_completeness IS NULL
            OR (
                ais_completeness >= 0.0
                AND ais_completeness <= 1.0
            )
        ),

    CONSTRAINT vessel_tracks_track_continuity_check
        CHECK (
            track_continuity IS NULL
            OR (
                track_continuity >= 0.0
                AND track_continuity <= 1.0
            )
        ),

    CONSTRAINT vessel_tracks_spill_mmsi_unique
        UNIQUE (spill_id, mmsi)
);

CREATE INDEX IF NOT EXISTS idx_vessel_tracks_geometry_gist
    ON vessel_tracks
    USING GIST (track_geometry);

CREATE INDEX IF NOT EXISTS idx_vessel_tracks_spill_time
    ON vessel_tracks (spill_id, track_start_time, track_end_time);

CREATE INDEX IF NOT EXISTS idx_vessel_tracks_mmsi
    ON vessel_tracks (mmsi);

CREATE INDEX IF NOT EXISTS idx_vessel_tracks_gap_statistics_gin
    ON vessel_tracks
    USING GIN (gap_statistics);

CREATE TABLE IF NOT EXISTS data_quality_reports (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    spill_id BIGINT,

    report_type TEXT NOT NULL,

    report_version TEXT NOT NULL DEFAULT '1.0',

    status TEXT NOT NULL,

    report_path TEXT,

    source_file TEXT,

    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,

    limitations JSONB NOT NULL DEFAULT '[]'::jsonb,

    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT data_quality_reports_spill_fk
        FOREIGN KEY (spill_id)
        REFERENCES spill_events (id)
        ON DELETE CASCADE,

    CONSTRAINT data_quality_reports_report_type_check
        CHECK (
            report_type IN (
                'ais_etl',
                'ais_parquet_validation',
                'scenario_compatibility',
                'sar_metadata',
                'drift_metadata',
                'candidate_ranking'
            )
        ),

    CONSTRAINT data_quality_reports_status_check
        CHECK (
            status IN (
                'pass',
                'warning',
                'fail',
                'blocked',
                'unavailable'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_data_quality_reports_spill_type
    ON data_quality_reports (spill_id, report_type);

CREATE INDEX IF NOT EXISTS idx_data_quality_reports_status
    ON data_quality_reports (status);

CREATE INDEX IF NOT EXISTS idx_data_quality_reports_metrics_gin
    ON data_quality_reports
    USING GIN (metrics);

CREATE TABLE IF NOT EXISTS audit_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    spill_id BIGINT,

    event_type TEXT NOT NULL,

    event_status TEXT NOT NULL,

    actor TEXT NOT NULL,

    message TEXT NOT NULL,

    details JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT audit_events_spill_fk
        FOREIGN KEY (spill_id)
        REFERENCES spill_events (id)
        ON DELETE CASCADE,

    CONSTRAINT audit_events_status_check
        CHECK (
            event_status IN (
                'started',
                'completed',
                'warning',
                'blocked',
                'failed'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_audit_events_spill_created_at
    ON audit_events (spill_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_event_type
    ON audit_events (event_type);

CREATE INDEX IF NOT EXISTS idx_audit_events_details_gin
    ON audit_events
    USING GIN (details);

COMMIT;