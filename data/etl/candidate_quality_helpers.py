import json
from pathlib import Path
from typing import Any, Dict

# Adjust if your layout differs
BASE_DIR = Path(__file__).resolve().parents[2]  # SpillTrace-SIH26 root
DEFAULT_QUALITY_PATH = BASE_DIR / "data" / "ais" / "reports" / "ais_sample_10000_quality_report_with_scenario.json"

def compute_ais_completeness_and_continuity(
    mmsi: str,
    quality_path: Path = DEFAULT_QUALITY_PATH,
) -> Dict[str, Any]:
    """
    For Day 8, compute simple AIS quality proxies per candidate (MMSI).
    
    This is a placeholder implementation using global AIS stats.
    Later, you can refine this to be per-MMSI using vessel_tracks or ais_positions.
    
    Returns a dict with:
      - ais_completeness
      - track_continuity
      - gap_stats
      - source_file
      - cleaned_parquet_path
      - etl_report_path
      - data_quality_status
      - lineage_id
    """
    with open(quality_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    gap_stats_sec = data.get("gap_statistics_seconds", {})
    gap_count = gap_stats_sec.get("gap_count", 0)
    max_gap_s = gap_stats_sec.get("max_gap", 0.0)
    median_gap_s = gap_stats_sec.get("median_gap", 0.0)

    # Convert to minutes for backend contract
    max_gap_min = max_gap_s / 60.0 if max_gap_s else 0.0
    median_gap_min = median_gap_s / 60.0 if median_gap_s else 0.0
    # For mean gap, approximate using median (refine later with per-MMSI stats)
    mean_gap_min = median_gap_min

    cleaned_rows = data.get("cleaned_row_count", 0)
    input_rows = data.get("input_row_count", 0)

    # Simple completeness proxy: ratio of cleaned rows to input rows
    ais_completeness = (cleaned_rows / input_rows) if input_rows > 0 else 0.0

    # Simple continuity proxy: 1 - (gap_count / cleaned_rows), clipped to [0,1]
    if cleaned_rows > 0:
        continuity_raw = 1.0 - (gap_count / cleaned_rows)
        track_continuity = max(0.0, min(1.0, continuity_raw))
    else:
        track_continuity = 0.0

    # Data quality status based on compatibility and gaps
    compatibility_status = data.get("compatibility_status", "PASS")
    if compatibility_status == "BLOCKED":
        data_quality_status = "BLOCKED"
    elif max_gap_s > 3600:  # > 1 hour max gap as an example rule
        data_quality_status = "WARN"
    else:
        data_quality_status = "PASS"

    source_file = data.get("input_file", "")
    cleaned_parquet_path = data.get("output_file", "")
    etl_report_path = str(quality_path.relative_to(BASE_DIR))

    spill_id = data.get("spill_id", "UNKNOWN")
    lineage_id = f"lineage_{spill_id}_ais_v1_mmsi_{mmsi}"

    return {
        "ais_completeness": round(ais_completeness, 4),
        "track_continuity": round(track_continuity, 4),
        "gap_stats": {
            "gap_count": gap_count,
            "max_gap_minutes": round(max_gap_min, 2),
            "mean_gap_minutes": round(mean_gap_min, 2),
            "total_gap_minutes": round((max_gap_min + mean_gap_min) / 2.0, 2),  # placeholder
        },
        "source_file": source_file,
        "cleaned_parquet_path": cleaned_parquet_path,
        "etl_report_path": etl_report_path,
        "data_quality_status": data_quality_status,
        "lineage_id": lineage_id,
    }

if __name__ == "__main__":
    import pprint
    result = compute_ais_completeness_and_continuity("123456789")
    pprint.pprint(result)