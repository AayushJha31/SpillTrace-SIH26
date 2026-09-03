import json
from pathlib import Path

from data.queries.get_drift_ais_filter_result import (
    get_drift_ais_filter_result,
)


def write_compatibility_report(
    path: Path,
    spill_id: str,
    compatibility_state: str,
    candidate_ranking_enabled: bool,
    blocking_reasons: list[dict],
) -> None:
    report = {
        "spill_id": spill_id,
        "compatibility_state": compatibility_state,
        "candidate_ranking_enabled": candidate_ranking_enabled,
        "blocking_reasons": blocking_reasons,
    }

    path.write_text(
        json.dumps(report),
        encoding="utf-8",
    )


def test_blocked_scenario_returns_409_and_no_tracks(
    tmp_path: Path,
) -> None:
    report_file = tmp_path / "compatibility_report.json"

    write_compatibility_report(
        path=report_file,
        spill_id="SPILL_TEST3_001",
        compatibility_state="insufficient_data",
        candidate_ranking_enabled=False,
        blocking_reasons=[
            {
                "code": "AIS_TEMPORAL_COVERAGE_MISMATCH",
                "message": "AIS does not overlap the origin-time window.",
            }
        ],
    )

    result = get_drift_ais_filter_result(
        spill_id="SPILL_TEST3_001",
        compatibility_report_file=report_file,
    )

    assert result["http_status_code"] == 409
    assert result["compatibility_state"] == "insufficient_data"
    assert result["candidate_ranking_enabled"] is False
    assert result["ais_quality_status"]["status"] == "unavailable"
    assert result["ais_quality_status"]["track_count"] == 0
    assert result["ais_quality_status"]["quality_fields"] == {
    "ais_completeness": None,
    "track_continuity": None,
    "gap_statistics": None,
    "source_provenance": None,
}
    assert result["detail"]["code"] == "AIS_TEMPORAL_COVERAGE_MISMATCH"
    assert result["detail"]["spill_id"] == "SPILL_TEST3_001"
    assert result["tracks"]["type"] == "FeatureCollection"
    assert result["tracks"]["features"] == []


def test_requested_spill_id_must_match_report(
    tmp_path: Path,
) -> None:
    report_file = tmp_path / "compatibility_report.json"

    write_compatibility_report(
        path=report_file,
        spill_id="SPILL_TEST3_001",
        compatibility_state="insufficient_data",
        candidate_ranking_enabled=False,
        blocking_reasons=[],
    )

    try:
        get_drift_ais_filter_result(
            spill_id="DIFFERENT_SPILL_ID",
            compatibility_report_file=report_file,
        )
    except ValueError as error:
        assert "does not match compatibility report" in str(error)
    else:
        raise AssertionError(
            "Expected ValueError for a mismatched spill ID."
        )


def test_missing_compatibility_report_fails_safely(
    tmp_path: Path,
) -> None:
    missing_report_file = tmp_path / "missing_report.json"

    try:
        get_drift_ais_filter_result(
            spill_id="SPILL_TEST3_001",
            compatibility_report_file=missing_report_file,
        )
    except FileNotFoundError as error:
        assert "Compatibility report not found" in str(error)
    else:
        raise AssertionError(
            "Expected FileNotFoundError for a missing compatibility report."
        )