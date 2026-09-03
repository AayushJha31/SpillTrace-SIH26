EXPLAIN (ANALYZE, BUFFERS)
WITH query_parameters AS (
    SELECT
        -90.10000::double precision AS min_longitude,
        -89.90000::double precision AS max_longitude,
        29.70000::double precision AS min_latitude,
        30.00000::double precision AS max_latitude,
        '2025-01-08T00:00:00Z'::timestamptz AS start_utc,
        '2025-01-08T00:10:00Z'::timestamptz AS end_utc
),
filtered_positions AS (
    SELECT
        a.mmsi,
        a.observed_at,
        a.latitude,
        a.longitude,
        a.position,
        a.sog_knots,
        a.cog_degrees,
        a.heading_degrees,
        a.source_file,
        a.source_row_number
    FROM ais_positions AS a
    CROSS JOIN query_parameters AS p
    WHERE a.observed_at BETWEEN p.start_utc AND p.end_utc
      AND a.longitude BETWEEN p.min_longitude AND p.max_longitude
      AND a.latitude BETWEEN p.min_latitude AND p.max_latitude
),
track_quality AS (
    SELECT
        mmsi,
        COUNT(*)::integer AS position_count,
        MIN(observed_at) AS track_start_time,
        MAX(observed_at) AS track_end_time,
        COUNT(*) FILTER (
            WHERE previous_observed_at IS NOT NULL
        )::integer AS gap_count,
        COALESCE(
            MAX(
                EXTRACT(
                    EPOCH FROM (
                        observed_at - previous_observed_at
                    )
                )
            ) FILTER (
                WHERE previous_observed_at IS NOT NULL
            ),
            0
        ) AS max_gap_seconds
    FROM (
        SELECT
            mmsi,
            observed_at,
            LAG(observed_at) OVER (
                PARTITION BY mmsi
                ORDER BY observed_at
            ) AS previous_observed_at
        FROM filtered_positions
    ) AS ordered_positions
    GROUP BY mmsi
),
track_geometries AS (
    SELECT
        mmsi,
        ST_MakeLine(
            position
            ORDER BY observed_at
        ) AS track_geometry,
        JSONB_AGG(
            JSONB_BUILD_OBJECT(
                'observed_at',
                to_char(
                    observed_at AT TIME ZONE 'UTC',
                    'YYYY-MM-DD"T"HH24:MI:SS"Z"'
                ),
                'longitude',
                longitude,
                'latitude',
                latitude,
                'sog_knots',
                sog_knots,
                'cog_degrees',
                cog_degrees,
                'heading_degrees',
                heading_degrees,
                'source_file',
                source_file,
                'source_row_number',
                source_row_number
            )
            ORDER BY observed_at
        ) AS positions
    FROM filtered_positions
    GROUP BY mmsi
)
SELECT
    t.mmsi,
    q.position_count,
    q.track_start_time,
    q.track_end_time,
    q.gap_count,
    q.max_gap_seconds,
    ST_AsGeoJSON(
        ST_Transform(t.track_geometry, 4326)
    )::jsonb AS geometry,
    t.positions
FROM track_geometries AS t
JOIN track_quality AS q
    ON q.mmsi = t.mmsi
WHERE q.position_count >= 2
ORDER BY
    q.position_count DESC,
    t.mmsi;