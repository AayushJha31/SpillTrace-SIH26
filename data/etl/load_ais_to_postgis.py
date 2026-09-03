from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import psycopg


PARQUET_FILE = Path(
    "data/ais/cleaned/ais_sample_10000_cleaned.parquet"
)

DATABASE_CONNECTION = (
    "host=localhost "
    "port=5432 "
    "dbname=spilltrace "
    "user=spilltrace "
    "password=spilltrace_local_password"
)

BATCH_SIZE = 1000


def nullable_float(value):
    if pd.isna(value):
        return None
    return float(value)


def nullable_int(value):
    if pd.isna(value):
        return None
    return int(value)


def parse_utc_timestamp(value: str) -> pd.Timestamp:
    timestamp = pd.to_datetime(value, utc=True, errors="raise")

    if pd.isna(timestamp):
        raise ValueError(f"Invalid UTC timestamp: {value}")

    return timestamp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Load a selected real AIS Parquet spatial-temporal subset "
            "into PostGIS."
        )
    )

    parser.add_argument(
        "--start-utc",
        required=True,
        help="Inclusive ISO 8601 UTC start, for example 2025-01-08T00:00:00Z",
    )

    parser.add_argument(
        "--end-utc",
        required=True,
        help="Inclusive ISO 8601 UTC end, for example 2025-01-08T00:10:00Z",
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

    return parser


def validate_bounds(arguments: argparse.Namespace) -> None:
    if arguments.start_utc > arguments.end_utc:
        raise ValueError("--start-utc must be earlier than or equal to --end-utc.")

    if arguments.min_longitude > arguments.max_longitude:
        raise ValueError("--min-longitude must be less than or equal to --max-longitude.")

    if arguments.min_latitude > arguments.max_latitude:
        raise ValueError("--min-latitude must be less than or equal to --max-latitude.")

    if not -180.0 <= arguments.min_longitude <= 180.0:
        raise ValueError("--min-longitude must be within [-180, 180].")

    if not -180.0 <= arguments.max_longitude <= 180.0:
        raise ValueError("--max-longitude must be within [-180, 180].")

    if not -90.0 <= arguments.min_latitude <= 90.0:
        raise ValueError("--min-latitude must be within [-90, 90].")

    if not -90.0 <= arguments.max_latitude <= 90.0:
        raise ValueError("--max-latitude must be within [-90, 90].")


def select_subset(
    dataframe: pd.DataFrame,
    start_utc: pd.Timestamp,
    end_utc: pd.Timestamp,
    min_longitude: float,
    max_longitude: float,
    min_latitude: float,
    max_latitude: float,
) -> pd.DataFrame:
    subset = dataframe.loc[
        dataframe["observed_at"].between(start_utc, end_utc)
        & dataframe["longitude"].between(
            min_longitude,
            max_longitude,
        )
        & dataframe["latitude"].between(
            min_latitude,
            max_latitude,
        )
    ].copy()

    return subset.sort_values(
        by=["mmsi", "observed_at"],
        kind="mergesort",
    ).reset_index(drop=True)


def main() -> None:
    parser = build_parser()
    arguments = parser.parse_args()

    arguments.start_utc = parse_utc_timestamp(arguments.start_utc)
    arguments.end_utc = parse_utc_timestamp(arguments.end_utc)

    validate_bounds(arguments)

    if not PARQUET_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned Parquet file not found: {PARQUET_FILE}"
        )

    dataframe = pd.read_parquet(PARQUET_FILE)

    required_columns = [
        "mmsi",
        "observed_at",
        "latitude",
        "longitude",
        "source_file",
        "source_row_number",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required Parquet columns: "
            + ", ".join(missing_columns)
        )

    subset = select_subset(
        dataframe=dataframe,
        start_utc=arguments.start_utc,
        end_utc=arguments.end_utc,
        min_longitude=arguments.min_longitude,
        max_longitude=arguments.max_longitude,
        min_latitude=arguments.min_latitude,
        max_latitude=arguments.max_latitude,
    )

    if subset.empty:
        print("\n=== POSTGIS AIS SELECTIVE LOAD ===")
        print("No real AIS rows matched the requested spatial-temporal subset.")
        print("No database rows were inserted.")
        return

    insert_sql = """
        INSERT INTO ais_positions (
            mmsi,
            observed_at,
            latitude,
            longitude,
            position,
            sog_knots,
            cog_degrees,
            heading_degrees,
            vessel_type,
            source_file,
            source_row_number
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326),
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        ON CONFLICT (
            mmsi,
            observed_at,
            latitude,
            longitude
        )
        DO NOTHING
    """

    rows = []

    for row in subset.itertuples(index=False):
        rows.append(
            (
                int(row.mmsi),
                row.observed_at.to_pydatetime(),
                float(row.latitude),
                float(row.longitude),
                float(row.longitude),
                float(row.latitude),
                nullable_float(row.sog_knots),
                nullable_float(row.cog_degrees),
                nullable_float(row.heading_degrees),
                nullable_int(row.vessel_type),
                str(row.source_file),
                int(row.source_row_number),
            )
        )

    print("\n=== POSTGIS AIS SELECTIVE LOAD STARTED ===")
    print(f"Source Parquet: {PARQUET_FILE}")
    print(
        "Requested time range: "
        f"{arguments.start_utc.isoformat()} to "
        f"{arguments.end_utc.isoformat()}"
    )
    print(
        "Requested bounds: "
        f"longitude [{arguments.min_longitude}, {arguments.max_longitude}], "
        f"latitude [{arguments.min_latitude}, {arguments.max_latitude}]"
    )
    print(f"Real AIS rows selected: {len(rows):,}")
    print(f"Selected unique MMSIs: {subset['mmsi'].nunique():,}")

    inserted_before = 0
    inserted_after = 0

    with psycopg.connect(DATABASE_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ais_positions;")
            inserted_before = cursor.fetchone()[0]

            for start in range(0, len(rows), BATCH_SIZE):
                batch = rows[start:start + BATCH_SIZE]

                cursor.executemany(insert_sql, batch)

                print(
                    "Processed rows "
                    f"{start + 1:,} to "
                    f"{start + len(batch):,}"
                )

            connection.commit()

            cursor.execute("SELECT COUNT(*) FROM ais_positions;")
            inserted_after = cursor.fetchone()[0]

    print("\n=== POSTGIS AIS SELECTIVE LOAD COMPLETED ===")
    print(f"Rows in DB before load: {inserted_before:,}")
    print(f"Rows in DB after load: {inserted_after:,}")
    print(
        "New rows inserted: "
        f"{inserted_after - inserted_before:,}"
    )


if __name__ == "__main__":
    main()