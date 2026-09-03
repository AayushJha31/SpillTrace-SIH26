import json
from pathlib import Path

import pandas as pd
import pytest

from data.etl.load_ais_data import run_ais_etl


def write_fixture_csv(path: Path) -> None:
    rows = [
        {
            "mmsi": "987654321",
            "base_date_time": "2025-01-08T00:10:00Z",
            "latitude": 29.86105,
            "longitude": -90.01582,
            "sog": 12.5,
            "cog": 180.0,
            "heading": 180.0,
            "vessel_type": 70,
            "vessel_name": "TEST_VESSEL_A",
        },
        {
            "mmsi": "987654321",
            "base_date_time": "2025-01-08T00:00:00Z",
            "latitude": 29.86000,
            "longitude": -90.01000,
            "sog": 10.0,
            "cog": 175.0,
            "heading": 175.0,
            "vessel_type": 70,
            "vessel_name": "TEST_VESSEL_A",
        },
        {
            "mmsi": "987654321",
            "base_date_time": "2025-01-08T00:10:00Z",
            "latitude": 29.86105,
            "longitude": -90.01582,
            "sog": 12.5,
            "cog": 180.0,
            "heading": 180.0,
            "vessel_type": 70,
            "vessel_name": "TEST_VESSEL_A",
        },
        {
            "mmsi": "123456789",
            "base_date_time": "2025-01-08T00:05:00Z",
            "latitude": 29.87000,
            "longitude": -90.02000,
            "sog": 8.0,
            "cog": 90.0,
            "heading": 90.0,
            "vessel_type": 31,
            "vessel_name": "TEST_VESSEL_B",
        },
        {
            "mmsi": "invalid_mmsi",
            "base_date_time": "2025-01-08T00:06:00Z",
            "latitude": 29.87000,
            "longitude": -90.02000,
            "sog": 8.0,
            "cog": 90.0,
            "heading": 90.0,
            "vessel_type": 31,
            "vessel_name": "INVALID_MMSI",
        },
        {
            "mmsi": "234567891",
            "base_date_time": "not_a_timestamp",
            "latitude": 29.87000,
            "longitude": -90.02000,
            "sog": 8.0,
            "cog": 90.0,
            "heading": 90.0,
            "vessel_type": 31,
            "vessel_name": "INVALID_TIME",
        },
        {
            "mmsi": "345678912",
            "base_date_time": "2025-01-08T00:07:00Z",
            "latitude": 95.00000,
            "longitude": -90.02000,
            "sog": 8.0,
            "cog": 90.0,
            "heading": 90.0,
            "vessel_type": 31,
            "vessel_name": "INVALID_LATITUDE",
        },
        {
            "mmsi": "456789123",
            "base_date_time": "2025-01-08T00:08:00Z",
            "latitude": 29.87000,
            "longitude": -190.00000,
            "sog": 8.0,
            "cog": 90.0,
            "heading": 90.0,
            "vessel_type": 31,
            "vessel_name": "INVALID_LONGITUDE",
        },
    ]

    pd.DataFrame(rows).to_csv(path, index=False)


@pytest.fixture
def etl_paths(tmp_path: Path) -> dict[str, Path]:
    input_file = tmp_path / "ais_test_input.csv"
    output_file = tmp_path / "cleaned" / "ais_test_cleaned.parquet"
    report_file = tmp_path / "reports" / "ais_test_quality_report.json"

    write_fixture_csv(input_file)

    return {
        "input_file": input_file,
        "output_file": output_file,
        "report_file": report_file,
    }


def run_test_etl(etl_paths: dict[str, Path]) -> dict:
    return run_ais_etl(
        input_file=etl_paths["input_file"],
        output_file=etl_paths["output_file"],
        report_file=etl_paths["report_file"],
        source_file_label="tests/fixtures/ais_test_input.csv",
    )


def test_etl_rejects_invalid_rows_and_removes_duplicates(etl_paths):
    report = run_test_etl(etl_paths)

    assert report["input_row_count"] == 8
    assert report["rejected_required_field_count"] == 4
    assert report["valid_before_deduplication_count"] == 4
    assert report["rejection_counts"]["duplicate_observation"] == 1
    assert report["cleaned_row_count"] == 3

    assert report["rejection_counts"]["invalid_mmsi"] == 1
    assert report["rejection_counts"]["invalid_timestamp"] == 1
    assert report["rejection_counts"]["invalid_latitude"] == 1
    assert report["rejection_counts"]["invalid_longitude"] == 1

    assert (
        report["input_row_count"]
        == report["rejected_required_field_count"]
        + report["rejection_counts"]["duplicate_observation"]
        + report["cleaned_row_count"]
    )


def test_etl_writes_utc_sorted_parquet_and_gap_statistics(etl_paths):
    report = run_test_etl(etl_paths)

    assert etl_paths["output_file"].exists()
    assert etl_paths["report_file"].exists()

    cleaned = pd.read_parquet(etl_paths["output_file"])

    assert str(cleaned["mmsi"].dtype) == "Int64"
    assert isinstance(cleaned["observed_at"].dtype, pd.DatetimeTZDtype)
    assert str(cleaned["observed_at"].dt.tz) == "UTC"

    sorted_copy = cleaned.sort_values(
        by=["mmsi", "observed_at"],
        kind="mergesort",
    ).reset_index(drop=True)

    pd.testing.assert_frame_equal(cleaned, sorted_copy)

    vessel_a = cleaned.loc[
        cleaned["mmsi"] == 987654321
    ].sort_values("observed_at")

    assert len(vessel_a) == 2

    gap_seconds = (
        vessel_a["observed_at"]
        .diff()
        .dt.total_seconds()
        .dropna()
        .tolist()
    )

    assert gap_seconds == [600.0]
    assert report["gap_statistics_seconds"]["gap_count"] == 1
    assert report["gap_statistics_seconds"]["median_gap"] == 600.0
    assert report["gap_statistics_seconds"]["max_gap"] == 600.0
    assert report["gap_statistics_seconds"]["p95_gap"] == 600.0


def test_etl_preserves_source_lineage_and_coordinates(etl_paths):
    run_test_etl(etl_paths)

    cleaned = pd.read_parquet(etl_paths["output_file"])

    assert cleaned["source_file"].eq(
        "tests/fixtures/ais_test_input.csv"
    ).all()

    assert cleaned["source_row_number"].tolist() == [5, 3, 2]

    assert cleaned["latitude"].between(-90.0, 90.0).all()
    assert cleaned["longitude"].between(-180.0, 180.0).all()

    coordinates = [
        float(cleaned.iloc[0]["longitude"]),
        float(cleaned.iloc[0]["latitude"]),
    ]

    assert coordinates == [-90.02, 29.87]


def test_etl_writes_report_file_matching_returned_report(etl_paths):
    returned_report = run_test_etl(etl_paths)

    written_report = json.loads(
        etl_paths["report_file"].read_text(encoding="utf-8")
    )

    assert written_report == returned_report


def test_etl_fails_when_required_columns_are_missing(tmp_path):
    input_file = tmp_path / "missing_required_columns.csv"
    output_file = tmp_path / "cleaned.parquet"
    report_file = tmp_path / "report.json"

    pd.DataFrame(
        [
            {
                "mmsi": "987654321",
                "base_date_time": "2025-01-08T00:00:00Z",
                "latitude": 29.86105,
            }
        ]
    ).to_csv(input_file, index=False)

    with pytest.raises(ValueError, match="Missing required columns: longitude"):
        run_ais_etl(
            input_file=input_file,
            output_file=output_file,
            report_file=report_file,
            source_file_label="tests/fixtures/missing_required_columns.csv",
        )