from __future__ import annotations

import json
from pathlib import Path

import duckdb


PARQUET_FILE = Path(
    "data/ais/cleaned/ais_sample_10000_cleaned.parquet"
)

QUALITY_REPORT_FILE = Path(
    "data/ais/reports/ais_sample_10000_quality_report.json"
)

VALIDATION_REPORT_FILE = Path(
    "data/ais/reports/ais_sample_10000_parquet_validation.json"
)


def rows_to_dicts(cursor) -> list[dict]:
    columns = [column[0] for column in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def main() -> None:
    if not PARQUET_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned Parquet file not found: {PARQUET_FILE}"
        )

    if not QUALITY_REPORT_FILE.exists():
        raise FileNotFoundError(
            f"ETL quality report not found: {QUALITY_REPORT_FILE}"
        )

    quality_report = json.loads(
        QUALITY_REPORT_FILE.read_text(encoding="utf-8")
    )

    connection = duckdb.connect(database=":memory:")
    connection.execute("SET TimeZone='UTC'")

    parquet_path = PARQUET_FILE.as_posix().replace("'", "''")

    schema_cursor = connection.execute(
        f"""
        DESCRIBE
        SELECT *
        FROM read_parquet('{parquet_path}')
        """
    )

    schema = rows_to_dicts(schema_cursor)

    summary_cursor = connection.execute(
        f"""
        SELECT
            COUNT(*) AS cleaned_row_count,
            COUNT(DISTINCT mmsi) AS unique_mmsi_count,
            MIN(observed_at) AS first_timestamp_utc,
            MAX(observed_at) AS last_timestamp_utc,
            MIN(latitude) AS min_latitude,
            MAX(latitude) AS max_latitude,
            MIN(longitude) AS min_longitude,
            MAX(longitude) AS max_longitude,
            SUM(
                CASE
                    WHEN observed_at IS NULL
                    THEN 1
                    ELSE 0
                END
            ) AS null_observed_at_count,
            SUM(
                CASE
                    WHEN mmsi IS NULL
                    THEN 1
                    ELSE 0
                END
            ) AS null_mmsi_count,
            SUM(
                CASE
                    WHEN latitude IS NULL
                    THEN 1
                    ELSE 0
                END
            ) AS null_latitude_count,
            SUM(
                CASE
                    WHEN longitude IS NULL
                    THEN 1
                    ELSE 0
                END
            ) AS null_longitude_count,
            SUM(
                CASE
                    WHEN mmsi NOT BETWEEN 100000000 AND 999999999
                    THEN 1
                    ELSE 0
                END
            ) AS invalid_mmsi_count,
            SUM(
                CASE
                    WHEN latitude NOT BETWEEN -90.0 AND 90.0
                    THEN 1
                    ELSE 0
                END
            ) AS invalid_latitude_count,
            SUM(
                CASE
                    WHEN longitude NOT BETWEEN -180.0 AND 180.0
                    THEN 1
                    ELSE 0
                END
            ) AS invalid_longitude_count
        FROM read_parquet('{parquet_path}')
        """
    )

    summary = rows_to_dicts(summary_cursor)[0]

    duplicate_cursor = connection.execute(
        f"""
        SELECT COUNT(*) AS duplicate_observation_count
        FROM (
            SELECT
                mmsi,
                observed_at,
                latitude,
                longitude
            FROM read_parquet('{parquet_path}')
            GROUP BY
                mmsi,
                observed_at,
                latitude,
                longitude
            HAVING COUNT(*) > 1
        )
        """
    )

    duplicate_summary = rows_to_dicts(duplicate_cursor)[0]

    ordering_cursor = connection.execute(
        f"""
        WITH numbered_rows AS (
            SELECT
                mmsi,
                observed_at,
                LAG(mmsi) OVER (
                    ORDER BY mmsi, observed_at
                ) AS previous_mmsi,
                LAG(observed_at) OVER (
                    ORDER BY mmsi, observed_at
                ) AS previous_observed_at
            FROM read_parquet('{parquet_path}')
        )
        SELECT COUNT(*) AS ordering_violation_count
        FROM numbered_rows
        WHERE
            previous_mmsi IS NOT NULL
            AND (
                mmsi < previous_mmsi
                OR (
                    mmsi = previous_mmsi
                    AND observed_at < previous_observed_at
                )
            )
        """
    )

    ordering_summary = rows_to_dicts(ordering_cursor)[0]

    expected_row_count = quality_report["cleaned_row_count"]
    expected_unique_mmsi_count = quality_report["unique_mmsi_count"]

    validation = {
        "parquet_file": str(PARQUET_FILE),
        "etl_quality_report_file": str(QUALITY_REPORT_FILE),
        "schema": schema,
        "summary": summary,
        "duplicate_check": duplicate_summary,
        "ordering_check": ordering_summary,
        "cross_checks": {
            "cleaned_row_count_matches_etl_report": (
                summary["cleaned_row_count"] == expected_row_count
            ),
            "unique_mmsi_count_matches_etl_report": (
                summary["unique_mmsi_count"]
                == expected_unique_mmsi_count
            ),
            "no_null_required_fields": (
                summary["null_observed_at_count"] == 0
                and summary["null_mmsi_count"] == 0
                and summary["null_latitude_count"] == 0
                and summary["null_longitude_count"] == 0
            ),
            "no_invalid_mmsi": (
                summary["invalid_mmsi_count"] == 0
            ),
            "no_invalid_latitude": (
                summary["invalid_latitude_count"] == 0
            ),
            "no_invalid_longitude": (
                summary["invalid_longitude_count"] == 0
            ),
            "no_duplicate_observations": (
                duplicate_summary["duplicate_observation_count"] == 0
            ),
            "sorted_by_mmsi_then_observed_at": (
                ordering_summary["ordering_violation_count"] == 0
            ),
        },
    }

    VALIDATION_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    VALIDATION_REPORT_FILE.write_text(
        json.dumps(
            validation,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print("\n=== CLEANED AIS PARQUET VALIDATION ===")
    print(f"Rows: {summary['cleaned_row_count']:,}")
    print(f"Unique MMSIs: {summary['unique_mmsi_count']:,}")
    print(
        "Time range: "
        f"{summary['first_timestamp_utc']} to "
        f"{summary['last_timestamp_utc']}"
    )
    print(
        "Bounds: "
        f"longitude [{summary['min_longitude']}, "
        f"{summary['max_longitude']}], "
        f"latitude [{summary['min_latitude']}, "
        f"{summary['max_latitude']}]"
    )
    print(
        "Duplicate groups remaining: "
        f"{duplicate_summary['duplicate_observation_count']}"
    )
    print(
        "Ordering violations: "
        f"{ordering_summary['ordering_violation_count']}"
    )
    print(
        "Validation report: "
        f"{VALIDATION_REPORT_FILE}"
    )

    failed_checks = [
        name
        for name, passed in validation["cross_checks"].items()
        if not passed
    ]

    if failed_checks:
        raise RuntimeError(
            "Parquet validation failed: "
            + ", ".join(failed_checks)
        )

    print("All Parquet validation checks passed.")


if __name__ == "__main__":
    main()