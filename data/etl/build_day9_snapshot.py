import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

QUALITY_PATH = (
    BASE_DIR
    / "data"
    / "ais"
    / "reports"
    / "ais_sample_10000_quality_report_with_scenario.json"
)

OUTPUT_PATH = BASE_DIR / "data" / "ais" / "reports" / "day9_snapshot.json"


def build_snapshot() -> None:
    with QUALITY_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    snapshot = {
        "day": 9,
        "spill_id": data.get("spill_id"),
        "data_mode": data.get("data_mode"),
        "compatibility_status": data.get("compatibility_status"),
        "candidate_ranking_enabled": data.get("candidate_ranking_enabled"),
        "source_file": data.get("input_file"),
        "cleaned_parquet_path": data.get("output_file"),
        "quality_report_path": str(QUALITY_PATH.relative_to(BASE_DIR)),
        "rows": {
            "input_rows": data.get("input_row_count"),
            "cleaned_rows": data.get("cleaned_row_count"),
            "unique_mmsi_count": data.get("unique_mmsi_count"),
        },
        "time_range": {
            "first_timestamp_utc": data.get("first_timestamp_utc"),
            "last_timestamp_utc": data.get("last_timestamp_utc"),
        },
        "gap_statistics_seconds": data.get("gap_statistics_seconds"),
        "scenario_context": {
            "sar_acquisition_start_utc": data.get("sar_acquisition_start_utc"),
            "sar_acquisition_end_utc": data.get("sar_acquisition_end_utc"),
            "origin_time_window_start_utc": data.get("origin_time_window_start_utc"),
            "origin_time_window_end_utc": data.get("origin_time_window_end_utc"),
            "temporal_overlap_with_scenario": data.get("temporal_overlap_with_scenario"),
        },
        "limitations": [
            "Development subset (10,000 rows); not representative of national-scale AIS.",
            "Explicitly incompatible with SPILL_TEST3_001; candidate ranking disabled.",
            "No synthetic positions created; large gaps are reported, not interpolated.",
        ],
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(snapshot, file, indent=2)

    print(f"Written: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_snapshot()