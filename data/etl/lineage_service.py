import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

# Adjust if your layout differs
BASE_DIR = Path(__file__).resolve().parents[2]  # SpillTrace-SIH26 root
DEFAULT_QUALITY_PATH = BASE_DIR / "data" / "ais" / "reports" / "ais_sample_10000_quality_report_with_scenario.json"

# You can later replace these with real git sha / config versions
CODE_VERSION = "spilltrace-de-v1.0.0-day8"
CONFIG_VERSION = "ais-etl-v1"

def get_lineage_report(
    spill_id: str,
    mmsi: str | None = None,
    quality_path: Path = DEFAULT_QUALITY_PATH,
) -> Dict[str, Any]:
    """
    Return a lineage report dict suitable for Aayush's /api/v1/spills/{spill_id}/lineage endpoint.
    
    For Day 8, we assume one global AIS lineage per demo scenario.
    Later, this can be extended to select by spill_id, mmsi, or source_file.
    """
    with open(quality_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    source_file = data.get("input_file", "")
    cleaned_parquet_path = data.get("output_file", "")
    etl_report_path = str(quality_path.relative_to(BASE_DIR))
    quality_report_path = str(quality_path.relative_to(BASE_DIR))

    lineage_id = f"lineage_{data.get('spill_id', spill_id)}_ais_v1"
    if mmsi:
        lineage_id += f"_mmsi_{mmsi}"

    report = {
        "spill_id": data.get("spill_id", spill_id),
        "mmsi": mmsi,
        "lineage_id": lineage_id,
        "data_mode": data.get("data_mode", "REAL"),
        "source_file": source_file,
        "cleaned_parquet_path": cleaned_parquet_path,
        "etl_report_path": etl_report_path,
        "quality_report_path": quality_report_path,
        "processing_metadata": {
            "code_version": CODE_VERSION,
            "config_version": CONFIG_VERSION,
            "processing_timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "input_row_count": data.get("input_row_count"),
            "cleaned_row_count": data.get("cleaned_row_count"),
            "unique_mmsi_count": data.get("unique_mmsi_count"),
        },
        "provenance": {
            "ais_source": source_file,
            "cleaned_ais_parquet": cleaned_parquet_path,
            "etl_quality_report": etl_report_path,
        },
    }

    return report

if __name__ == "__main__":
    # Simple local test
    import pprint
    report = get_lineage_report("SPILL_DEMO_001", mmsi="123456789")
    pprint.pprint(report)