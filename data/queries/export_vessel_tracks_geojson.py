from __future__ import annotations

import argparse
import json
from datetime import timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


DATABASE_CONNECTION = (
    "host=localhost "
    "port=5432 "
    "dbname=spilltrace "
    "user=spilltrace "
    "password=spilltrace_local_password"
)

DEFAULT_OUTPUT_FILE = Path(
    "data/ais/reports/vessel_tracks_feature_collection.geojson"
)


def parse_utc_timestamp(value: str):
    timestamp = value.replace("Z", "+00:00")
    parsed = __import__("datetime").datetime.fromisoformat(timestamp)

    if parsed.tzinfo is None:
        raise ValueError(
            "Timestamp must include UTC timezone information, for example "
            "2025-01-08T00:00:00Z."
        )

    return parsed.astimezone(timezone.utc)


def format_utc(value) -> str:
    return value.astimezone(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export selected real AIS vessel tracks as a GeoJSON "
            "FeatureCollection."
        )
    )

    parser.add_argument(
        "--start-utc",
        required=True,
        help="Inclusive ISO 8601 UTC start timestamp.",
    )

    parser.add_argument(
        "--end-utc",
        required=True,
        help="Inclusive ISO 8601 UTC end timestamp.",
    )

    parser.add_argument(
        "--min-longitude",
        required=True,
        type=float,
        help="Minimum longitude in EPSG:4326.",
    )

    parser.add_argument(
        "--max-longitude",
        required=True,
        type=float,
        help="Maximum longitude in EPSG:4326.",
    )

    parser.add_argument(
        "--min-latitude",
        required=True,
        type=float,
        help="Minimum latitude in EPSG:4326.",
    )

    parser.add_argument(
        "--max-latitude",
        required=True,
        type=float,
        help="Maximum latitude in EPSG:4326.",
    )

    parser.add_argument(
        "--output-file",
        default=str(DEFAULT_OUTPUT_FILE),
        help="Output GeoJSON path.",
    )

    return parser


def validate_arguments(arguments: argparse.Namespace) -> None:
    if arguments.start_utc > arguments.end_utc:
        raise ValueError("--start-utc must not be after --end-utc.")

    if arguments.min_longitude > arguments.max_longitude:
        raise ValueError(
            "--min-longitude must not be greater than --max-longitude."
        )

    if arguments.min_latitude > arguments.max_latitude:
        raise ValueError(
            "--min-latitude must not be greater than --max-latitude."
        )

    if not -180 <= arguments.min_longitude <= 180:
        raise ValueError("--min-longitude must be within [-180, 180].")

    if not -180 <= arguments.max_longitude <= 180:
        raise ValueError("--max-longitude must be within [-180, 180].")

    if not -90 <= arguments.min_latitude <= 90:
        raise ValueError("--min-latitude must be within [-90, 90].")

    if not -90 <= arguments.max_latitude <= 90:
        raise ValueError("--max-latitude must be within [-90, 90].")


def main() -> None:
    parser = build_parser()
    arguments = parser.parse_args()

    arguments.start_utc = parse_utc_timestamp(arguments.start_utc)
    arguments.end_utc = parse_utc_timestamp(arguments.end_utc)

    validate_arguments(arguments)

    output_file = Path(arguments.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    query = """
        WITH query_parameters AS (
            SELECT
                ST_MakeEnvelope(
                    %(min_longitude)s,
                    %(min_latitude)s,
                    %(max_longitude)s,
                    %(max_latitude)s,
                    4326
                ) AS query_bounds,
                %(start_utc)s::timestamptz AS start_utc,
                %(end_utc)s::timestamptz AS end_utc
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
              AND a.position && p.query_bounds
              AND ST_Intersects(a.position, p.query_bounds)
        ),
        ordered_positions AS (
            SELECT
                *,
                LAG(observed_at) OVER (
                    PARTITION BY mmsi
                    ORDER BY observed_at
                ) AS previous_observed_at
            FROM filtered_positions
        ),
        track_quality AS (
            SELECT
                mmsi,
                COUNT(*)::integer AS position_count,
                MIN(observed_at) AS track_start_time,
                MAX(observed_at) AS track_end_time,
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
                ) AS max_gap_seconds,
                COUNT(*) FILTER (
                    WHERE previous_observed_at IS NOT NULL
                )::integer AS gap_count
            FROM ordered_positions
            GROUP BY mmsi
        ),
        tracks AS (
            SELECT
                o.mmsi,
                ST_AsGeoJSON(
                    ST_MakeLine(
                        o.position
                        ORDER BY o.observed_at
                    )
                )::jsonb AS geometry,
                JSONB_AGG(
                    JSONB_BUILD_OBJECT(
                        'observed_at',
                        to_char(
                            o.observed_at AT TIME ZONE 'UTC',
                            'YYYY-MM-DD"T"HH24:MI:SS"Z"'
                        ),
                        'longitude',
                        o.longitude,
                        'latitude',
                        o.latitude,
                        'sog_knots',
                        o.sog_knots,
                        'cog_degrees',
                        o.cog_degrees,
                        'heading_degrees',
                        o.heading_degrees,
                        'source_file',
                        o.source_file,
                        'source_row_number',
                        o.source_row_number
                    )
                    ORDER BY o.observed_at
                ) AS positions,
                MIN(o.source_file) AS source_file
            FROM ordered_positions AS o
            GROUP BY o.mmsi
        )
        SELECT
            t.mmsi,
            t.geometry,
            t.positions,
            t.source_file,
            q.position_count,
            q.track_start_time,
            q.track_end_time,
            q.gap_count,
            q.max_gap_seconds
        FROM tracks AS t
        JOIN track_quality AS q
            ON q.mmsi = t.mmsi
        WHERE q.position_count >= 2
        ORDER BY
            q.position_count DESC,
            t.mmsi;
    """

    parameters = {
        "start_utc": arguments.start_utc,
        "end_utc": arguments.end_utc,
        "min_longitude": arguments.min_longitude,
        "max_longitude": arguments.max_longitude,
        "min_latitude": arguments.min_latitude,
        "max_latitude": arguments.max_latitude,
    }

    with psycopg.connect(
        DATABASE_CONNECTION,
        row_factory=dict_row,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            rows = cursor.fetchall()

    features = []

    for row in rows:
        position_count = int(row["position_count"])
        gap_count = int(row["gap_count"])
        max_gap_seconds = float(row["max_gap_seconds"])

        track_continuity_score = (
            1.0
            if position_count < 2 or max_gap_seconds == 0
            else 1.0 / (1.0 + max_gap_seconds / 300.0)
        )

        ais_completeness = (
            1.0
            if position_count >= 2
            else 0.0
        )

        features.append(
            {
                "type": "Feature",
                "geometry": row["geometry"],
                "properties": {
                    "mmsi": str(row["mmsi"]),
                    "track_start_time": format_utc(
                        row["track_start_time"]
                    ),
                    "track_end_time": format_utc(
                        row["track_end_time"]
                    ),
                    "position_count": position_count,
                    "gap_count": gap_count,
                    "max_gap_seconds": max_gap_seconds,
                    "track_continuity": round(
                        track_continuity_score,
                        6,
                    ),
                    "ais_completeness": ais_completeness,
                    "source_file": row["source_file"],
                    "positions": row["positions"],
                    "data_mode": (
                        "Real AIS development subset; "
                        "not compatible with SPILL_TEST3_001."
                    ),
                },
            }
        )

    feature_collection = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "source": "real AIS development subset",
            "crs": "EPSG:4326",
            "coordinate_order": "[longitude, latitude]",
            "start_utc": format_utc(arguments.start_utc),
            "end_utc": format_utc(arguments.end_utc),
            "bounds": {
                "min_longitude": arguments.min_longitude,
                "max_longitude": arguments.max_longitude,
                "min_latitude": arguments.min_latitude,
                "max_latitude": arguments.max_latitude,
            },
            "candidate_ranking_enabled": False,
            "compatibility_state": "insufficient_data",
            "limitation": (
                "This export is for AIS ETL, map, and query development. "
                "It must not be used as vessel-attribution evidence for "
                "SPILL_TEST3_001."
            ),
        },
    }

    output_file.write_text(
        json.dumps(feature_collection, indent=2),
        encoding="utf-8",
    )

    print("\n=== AIS TRACK GEOJSON EXPORT ===")
    print(f"Real tracks exported: {len(features):,}")
    print(f"Output file: {output_file}")
    print("Coordinate order: [longitude, latitude]")
    print("Candidate ranking enabled: false")
    print("Compatibility state: insufficient_data")


if __name__ == "__main__":
    main()