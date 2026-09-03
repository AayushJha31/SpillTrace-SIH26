from __future__ import annotations

import json
from pathlib import Path


MANIFEST_FILE = Path("data/manifests/scenario_manifest.json")

COMPATIBILITY_REPORT_FILE = Path(
    "data/manifests/scenario_compatibility_report.json"
)


def parse_utc_timestamp(value: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(
            "Timestamp must be an ISO 8601 UTC string ending in Z: "
            f"{value}"
        )

    return value


def validate_coordinate_pair(
    coordinates: list[float],
    field_name: str,
) -> list[str]:
    errors = []

    if not isinstance(coordinates, list) or len(coordinates) != 2:
        return [
            f"{field_name} must be a GeoJSON coordinate pair "
            "[longitude, latitude]."
        ]

    longitude, latitude = coordinates

    if not isinstance(longitude, (int, float)):
        errors.append(f"{field_name} longitude must be numeric.")
    elif not -180.0 <= longitude <= 180.0:
        errors.append(f"{field_name} longitude is outside [-180, 180].")

    if not isinstance(latitude, (int, float)):
        errors.append(f"{field_name} latitude must be numeric.")
    elif not -90.0 <= latitude <= 90.0:
        errors.append(f"{field_name} latitude is outside [-90, 90].")

    return errors


def main() -> None:
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            f"Scenario manifest not found: {MANIFEST_FILE}"
        )

    manifest = json.loads(
        MANIFEST_FILE.read_text(encoding="utf-8")
    )

    errors: list[str] = []
    warnings: list[str] = []
    blocking_reasons: list[dict] = []

    spill_id = manifest.get("spill_id")

    if not spill_id:
        errors.append("spill_id is required.")

    sar = manifest.get("sar", {})
    drift = manifest.get("drift", {})
    ais = manifest.get("ais", {})

    if sar.get("source_crs") != "EPSG:4326":
        errors.append(
            "SAR source CRS must be EPSG:4326 for this prototype contract."
        )

    if sar.get("output_crs") != "EPSG:4326":
        errors.append(
            "SAR output CRS must be EPSG:4326 for GeoJSON output."
        )

    observed_centroid = sar.get(
        "observed_slick_centroid",
        {},
    ).get("coordinates")

    errors.extend(
        validate_coordinate_pair(
            observed_centroid,
            "sar.observed_slick_centroid.coordinates",
        )
    )

    origin_point = drift.get(
        "origin_point",
        {},
    ).get("coordinates")

    errors.extend(
        validate_coordinate_pair(
            origin_point,
            "drift.origin_point.coordinates",
        )
    )

    try:
        parse_utc_timestamp(sar.get("acquisition_start_utc"))
        parse_utc_timestamp(sar.get("acquisition_end_utc"))
        parse_utc_timestamp(
            drift.get("origin_time_window", {}).get("start_utc")
        )
        parse_utc_timestamp(
            drift.get("origin_time_window", {}).get("end_utc")
        )
        parse_utc_timestamp(
            ais.get("data_time_range", {}).get("start_utc")
        )
        parse_utc_timestamp(
            ais.get("data_time_range", {}).get("end_utc")
        )
    except ValueError as error:
        errors.append(str(error))

    if sar.get("georeferencing_status") != "independently_verified":
        warnings.append(
            "SAR georeferencing is not independently verified."
        )
        blocking_reasons.append(
            {
                "code": "PROTOTYPE_GEOREFERENCING_LIMITATION",
                "message": (
                    "The scenario uses prototype injected coordinates and "
                    "must not be presented as independently ground-truth-verified."
                ),
            }
        )

    if drift.get("mode") != "Data-Backed Environmental Mode":
        warnings.append(
            "Drift mode is not data-backed environmental mode."
        )
        blocking_reasons.append(
            {
                "code": "ENVIRONMENTAL_FORCING_NOT_DATA_BACKED",
                "message": (
                    "Wind and current forcing are analyst-parameter-driven "
                    "or lack independently verifiable source metadata."
                ),
            }
        )

    wind_source = drift.get("wind", {}).get("source", "")
    current_source = drift.get("current", {}).get("source", "")

    if (
        not wind_source
        or not current_source
        or "unavailable" in wind_source.lower()
        or "unavailable" in current_source.lower()
    ):
        warnings.append(
            "Wind/current forcing source metadata is unavailable."
        )

    origin_window = drift.get("origin_time_window", {})
    ais_range = ais.get("data_time_range", {})

    origin_start = origin_window.get("start_utc", "")
    origin_end = origin_window.get("end_utc", "")
    ais_start = ais_range.get("start_utc", "")
    ais_end = ais_range.get("end_utc", "")

    temporal_overlap = (
        bool(origin_start)
        and bool(origin_end)
        and bool(ais_start)
        and bool(ais_end)
        and ais_start <= origin_end
        and ais_end >= origin_start
    )

    if not temporal_overlap:
        blocking_reasons.append(
            {
                "code": "AIS_TEMPORAL_COVERAGE_MISMATCH",
                "message": (
                    "The AIS dataset time range does not overlap the "
                    "required drift origin-time window."
                ),
            }
        )

    compatible = not errors and not blocking_reasons

    compatibility_state = (
        "compatible"
        if compatible
        else "insufficient_data"
    )

    report = {
        "spill_id": spill_id,
        "compatibility_state": compatibility_state,
        "candidate_ranking_enabled": compatible,
        "candidate_api_status_code": 200 if compatible else 409,
        "temporal_overlap": temporal_overlap,
        "errors": errors,
        "warnings": warnings,
        "blocking_reasons": blocking_reasons,
        "safe_user_message": (
            "AIS filtering and candidate ranking are available."
            if compatible
            else (
                "Vessel attribution is unavailable for this scenario. "
                "No vessel candidates have been generated."
            )
        ),
    }

    COMPATIBILITY_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    COMPATIBILITY_REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n=== SCENARIO COMPATIBILITY CHECK ===")
    print(f"Spill ID: {spill_id}")
    print(f"Compatibility state: {compatibility_state}")
    print(f"Temporal overlap: {temporal_overlap}")
    print(f"Candidate ranking enabled: {compatible}")
    print(
        "Expected candidate API status: "
        f"{report['candidate_api_status_code']}"
    )
    print(
        "Compatibility report: "
        f"{COMPATIBILITY_REPORT_FILE}"
    )

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")

    if blocking_reasons:
        print("\nBlocking reasons:")
        for reason in blocking_reasons:
            print(
                f"- {reason['code']}: "
                f"{reason['message']}"
            )


if __name__ == "__main__":
    main()