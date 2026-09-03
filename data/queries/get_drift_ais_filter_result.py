from __future__ import annotations

import json
from pathlib import Path

COMPATIBILITY_REPORT_FILE = Path("data/manifests/scenario_compatibility_report.json")


def get_drift_ais_filter_result(
    spill_id: str,
    compatibility_report_file: Path = COMPATIBILITY_REPORT_FILE,
) -> dict:
    if not compatibility_report_file.exists():
        raise FileNotFoundError(
            "Compatibility report not found: " f"{compatibility_report_file}"
        )

    report = json.loads(compatibility_report_file.read_text(encoding="utf-8"))

    if report.get("spill_id") != spill_id:
        raise ValueError(
            "Requested spill_id does not match compatibility report: " f"{spill_id}"
        )

    compatibility_state = report.get("compatibility_state")
    ranking_enabled = report.get("candidate_ranking_enabled", False)
    blocking_reasons = report.get("blocking_reasons", [])

    if compatibility_state != "compatible" or not ranking_enabled:
        primary_reason = (
            blocking_reasons[0]
            if blocking_reasons
            else {
                "code": "COMPATIBILITY_CHECK_FAILED",
                "message": (
                    "AIS filtering is unavailable because compatibility "
                    "requirements were not satisfied."
                ),
            }
        )

        return {
            "http_status_code": 409,
            "detail": {
                "code": primary_reason["code"],
                "message": (
                    "Vessel attribution is unavailable for this scenario. "
                    "No vessel candidates have been generated."
                ),
                "spill_id": spill_id,
            },
            "compatibility_state": compatibility_state,
            "candidate_ranking_enabled": False,
            "ais_quality_status": {
                "status": "unavailable",
                "reason": (
                    "No compatible AIS spatial-temporal subset is available "
                    "for this spill scenario; per-vessel completeness, "
                    "continuity, gap statistics, and source provenance "
                    "cannot be calculated."
                ),
                "track_count": 0,
                "quality_fields": {
                    "ais_completeness": None,
                    "track_continuity": None,
                    "gap_statistics": None,
                    "source_provenance": None,
                },
            },
            "blocking_reasons": blocking_reasons,
            "tracks": {
                "type": "FeatureCollection",
                "features": [],
            },
        }

    raise NotImplementedError(
        "Compatible drift-to-AIS filtering requires the actual corridor "
        "GeoJSON and compatible real AIS coverage."
    )


def main() -> None:
    result = get_drift_ais_filter_result("SPILL_TEST3_001")

    print("\n=== DRIFT-TO-AIS FILTER RESULT ===")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
