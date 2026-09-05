import json
from pathlib import Path
from typing import Any, Dict

# Adjust if your layout differs
BASE_DIR = Path(__file__).resolve().parents[2]  # SpillTrace-SIH26 root
DEFAULT_QUALITY_PATH = BASE_DIR / "data" / "ais" / "reports" / "ais_sample_10000_quality_report_with_scenario.json"

def get_quality_report(spill_id: str, quality_path: Path = DEFAULT_QUALITY_PATH) -> Dict[str, Any]:
    """
    Return a quality report dict suitable for Aayush's /api/v1/spills/{spill_id}/quality endpoint.
    
    For Day 8, we assume one global AIS quality report per demo scenario.
    Later, this can be extended to select by spill_id or source_file.
    """
    with open(quality_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic mapping to backend contract fields
    report = {
        "spill_id": data.get("spill_id", spill_id),
        "data_mode": data.get("data_mode", "REAL"),
        "compatibility_status": data.get("compatibility_status", "PASS"),
        "compatibility_reasons": data.get("compatibility_blockers", []),
        "source_file": data.get("input_file", ""),
        "cleaned_parquet_path": data.get("output_file", ""),
        "etl_report_path": str(quality_path.relative_to(BASE_DIR)),
        "quality_report_path": str(quality_path.relative_to(BASE_DIR)),
        "lineage_id": f"lineage_{data.get('spill_id', spill_id)}_ais_v1",
        "ais_metrics": {
            "input_rows": data.get("input_row_count"),
            "valid_before_deduplication_rows": data.get("valid_before_deduplication_count"),
            "cleaned_rows": data.get("cleaned_row_count"),
            "rejected_required_field_count": data.get("rejected_required_field_count"),
            "rejection_counts": data.get("rejection_counts", {}),
            "unique_mmsi_count": data.get("unique_mmsi_count"),
            "time_range": {
                "first_timestamp_utc": data.get("first_timestamp_utc"),
                "last_timestamp_utc": data.get("last_timestamp_utc"),
            },
            "gap_statistics_seconds": data.get("gap_statistics_seconds"),
        },
        "scenario_context": {
            "sar_acquisition_start_utc": data.get("sar_acquisition_start_utc"),
            "sar_acquisition_end_utc": data.get("sar_acquisition_end_utc"),
            "origin_time_window_start_utc": data.get("origin_time_window_start_utc"),
            "origin_time_window_end_utc": data.get("origin_time_window_end_utc"),
            "temporal_overlap_with_scenario": data.get("temporal_overlap_with_scenario"),
            "candidate_ranking_enabled": data.get("candidate_ranking_enabled"),
            "compatibility_blockers": data.get("compatibility_blockers"),
        },
    }

    return report

if __name__ == "__main__":
    # Simple local test
    import pprint
    report = get_quality_report("SPILL_DEMO_001")
    pprint.pprint(report)