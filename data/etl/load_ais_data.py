from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


INPUT_FILE = Path("data/ais/ais_sample_10000.csv")
OUTPUT_FILE = Path("data/ais/cleaned/ais_sample_10000_cleaned.parquet")
REPORT_FILE = Path("data/ais/reports/ais_sample_10000_quality_report.json")

SOURCE_FILE_LABEL = "data/ais/ais_sample_10000.csv"


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input AIS file not found: {INPUT_FILE}"
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(INPUT_FILE, low_memory=False)
    input_row_count = len(raw)

    df = raw.rename(
        columns={
            "base_date_time": "observed_at",
            "sog": "sog_knots",
            "cog": "cog_degrees",
            "heading": "heading_degrees",
        }
    ).copy()

    required_columns = [
        "mmsi",
        "observed_at",
        "latitude",
        "longitude",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    df["source_row_number"] = df.index + 2
    df["source_file"] = SOURCE_FILE_LABEL

    df["observed_at"] = pd.to_datetime(
        df["observed_at"],
        errors="coerce",
        utc=True,
    )

    df["mmsi"] = pd.to_numeric(
        df["mmsi"],
        errors="coerce",
    ).astype("Int64")

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce",
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce",
    )

    for column in [
        "sog_knots",
        "cog_degrees",
        "heading_degrees",
        "vessel_type",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    invalid_timestamp = df["observed_at"].isna()

    invalid_mmsi = (
        df["mmsi"].isna()
        | ~df["mmsi"].between(100000000, 999999999)
    )

    invalid_latitude = (
        df["latitude"].isna()
        | ~df["latitude"].between(-90.0, 90.0)
    )

    invalid_longitude = (
        df["longitude"].isna()
        | ~df["longitude"].between(-180.0, 180.0)
    )

    invalid_required_fields = (
        invalid_timestamp
        | invalid_mmsi
        | invalid_latitude
        | invalid_longitude
    )

    valid = df.loc[~invalid_required_fields].copy()

    duplicate_mask = valid.duplicated(
        subset=[
            "mmsi",
            "observed_at",
            "latitude",
            "longitude",
        ],
        keep="first",
    )

    duplicate_count = int(duplicate_mask.sum())

    cleaned = valid.loc[~duplicate_mask].copy()

    cleaned = cleaned.sort_values(
        by=["mmsi", "observed_at"],
        kind="mergesort",
    ).reset_index(drop=True)

    output_columns = [
        "mmsi",
        "observed_at",
        "latitude",
        "longitude",
        "sog_knots",
        "cog_degrees",
        "heading_degrees",
        "vessel_type",
        "vessel_name",
        "imo",
        "call_sign",
        "status",
        "length",
        "width",
        "draft",
        "cargo",
        "transceiver",
        "source_file",
        "source_row_number",
    ]

    existing_output_columns = [
        column
        for column in output_columns
        if column in cleaned.columns
    ]

    cleaned = cleaned[existing_output_columns]

    cleaned.to_parquet(
        OUTPUT_FILE,
        index=False,
        engine="pyarrow",
    )

    sorted_for_gaps = cleaned.sort_values(
        by=["mmsi", "observed_at"],
        kind="mergesort",
    )

    gaps_seconds = (
        sorted_for_gaps.groupby("mmsi")["observed_at"]
        .diff()
        .dt.total_seconds()
        .dropna()
    )

    report = {
        "input_file": SOURCE_FILE_LABEL,
        "output_file": str(OUTPUT_FILE),
        "input_row_count": int(input_row_count),
        "valid_before_deduplication_count": int(len(valid)),
        "cleaned_row_count": int(len(cleaned)),
        "rejected_required_field_count": int(
            invalid_required_fields.sum()
        ),
        "rejection_counts": {
            "invalid_timestamp": int(invalid_timestamp.sum()),
            "invalid_mmsi": int(invalid_mmsi.sum()),
            "invalid_latitude": int(invalid_latitude.sum()),
            "invalid_longitude": int(invalid_longitude.sum()),
            "duplicate_observation": duplicate_count,
        },
        "unique_mmsi_count": int(cleaned["mmsi"].nunique()),
        "first_timestamp_utc": (
            cleaned["observed_at"].min().isoformat()
        ),
        "last_timestamp_utc": (
            cleaned["observed_at"].max().isoformat()
        ),
        "gap_statistics_seconds": {
            "gap_count": int(len(gaps_seconds)),
            "max_gap": (
                float(gaps_seconds.max())
                if not gaps_seconds.empty
                else None
            ),
            "median_gap": (
                float(gaps_seconds.median())
                if not gaps_seconds.empty
                else None
            ),
            "p95_gap": (
                float(gaps_seconds.quantile(0.95))
                if not gaps_seconds.empty
                else None
            ),
        },
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n=== AIS ETL COMPLETED ===")
    print(f"Input rows: {input_row_count:,}")
    print(f"Valid rows before deduplication: {len(valid):,}")
    print(f"Duplicate rows removed: {duplicate_count:,}")
    print(f"Cleaned rows written: {len(cleaned):,}")
    print(f"Unique MMSIs: {cleaned['mmsi'].nunique():,}")
    print(f"Parquet output: {OUTPUT_FILE}")
    print(f"Quality report: {REPORT_FILE}")


if __name__ == "__main__":
    main()