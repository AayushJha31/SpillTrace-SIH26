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


def nullable_text(value):
    if pd.isna(value):
        return None
    return str(value)


def main() -> None:
    if not PARQUET_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned Parquet file not found: {PARQUET_FILE}"
        )

    df = pd.read_parquet(PARQUET_FILE)

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
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required Parquet columns: "
            + ", ".join(missing_columns)
        )

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

    for row in df.itertuples(index=False):
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

    print("\n=== POSTGIS AIS LOAD STARTED ===")
    print(f"Source Parquet: {PARQUET_FILE}")
    print(f"Rows prepared for loading: {len(rows):,}")

    inserted_before = 0
    inserted_after = 0

    with psycopg.connect(DATABASE_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM ais_positions;"
            )
            inserted_before = cursor.fetchone()[0]

            for start in range(0, len(rows), BATCH_SIZE):
                batch = rows[start:start + BATCH_SIZE]

                cursor.executemany(
                    insert_sql,
                    batch,
                )

                print(
                    "Processed rows "
                    f"{start + 1:,} to "
                    f"{start + len(batch):,}"
                )

            connection.commit()

            cursor.execute(
                "SELECT COUNT(*) FROM ais_positions;"
            )
            inserted_after = cursor.fetchone()[0]

    print("\n=== POSTGIS AIS LOAD COMPLETED ===")
    print(f"Rows in DB before load: {inserted_before:,}")
    print(f"Rows in DB after load: {inserted_after:,}")
    print(
        "New rows inserted: "
        f"{inserted_after - inserted_before:,}"
    )


if __name__ == "__main__":
    main()