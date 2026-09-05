import json
from pathlib import Path

# Paths (adjust if your layout differs)
BASE_DIR = Path(__file__).resolve().parents[2]  # SpillTrace-SIH26 root
QUALITY_REPORT_PATH = BASE_DIR / "data" / "ais" / "reports" / "ais_sample_10000_quality_report.json"
OUTPUT_PATH = BASE_DIR / "data" / "ais" / "reports" / "ais_sample_10000_quality_report_with_scenario.json"

# TODO: Replace these placeholders with real values from your scenario manifest / compatibility gate.
# For now, we use explicit placeholders so you can see what must be filled later.
SCENARIO_CONTEXT = {
    "spill_id": "SPILL_DEMO_001",
    "sar_acquisition_start_utc": "2025-01-08T00:00:00Z",
    "sar_acquisition_end_utc": "2025-01-08T01:00:00Z",
    "origin_time_window_start_utc": "2025-01-07T13:00:00Z",  # T-12h example
    "origin_time_window_end_utc": "2025-01-08T01:00:00Z",    # T-0h example
    "compatibility_status": "PASS",  # or "BLOCKED"
    "compatibility_blockers": [],    # e.g. ["temporal_mismatch", "geographic_mismatch"]
    "candidate_ranking_enabled": True,
    "data_mode": "REAL",             # or "TEST_FIXTURE"
}

def add_scenario_fields(quality_path: Path, output_path: Path, scenario: dict) -> None:
    with open(quality_path, "r", encoding="utf-8") as f:
        quality = json.load(f)

    # Basic overlap logic can be refined later; for now we derive from timestamps.
    ais_start = quality.get("first_timestamp_utc")
    ais_end = quality.get("last_timestamp_utc")

    temporal_overlap = None
    if ais_start and ais_end and scenario.get("origin_time_window_start_utc") and scenario.get("origin_time_window_end_utc"):
        # Simple string comparison is okay for ISO-8601 UTC; refine with datetime if needed.
        overlap = not (
            ais_end < scenario["origin_time_window_start_utc"]
            or ais_start > scenario["origin_time_window_end_utc"]
        )
        temporal_overlap = overlap

    enriched = {
        **quality,
        "spill_id": scenario["spill_id"],
        "sar_acquisition_start_utc": scenario["sar_acquisition_start_utc"],
        "sar_acquisition_end_utc": scenario["sar_acquisition_end_utc"],
        "origin_time_window_start_utc": scenario["origin_time_window_start_utc"],
        "origin_time_window_end_utc": scenario["origin_time_window_end_utc"],
        "temporal_overlap_with_scenario": temporal_overlap,
        "compatibility_status": scenario["compatibility_status"],
        "compatibility_blockers": scenario["compatibility_blockers"],
        "candidate_ranking_enabled": scenario["candidate_ranking_enabled"],
        "data_mode": scenario["data_mode"],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2)

    print(f"Enriched quality report written to: {output_path}")

if __name__ == "__main__":
    add_scenario_fields(QUALITY_REPORT_PATH, OUTPUT_PATH, SCENARIO_CONTEXT)