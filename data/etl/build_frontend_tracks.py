import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    BASE_DIR
    / "data"
    / "ais"
    / "reports"
    / "vessel_tracks_feature_collection.geojson"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "ais"
    / "reports"
    / "vessel_tracks_frontend.geojson"
)


def build_frontend_payload() -> None:
    with INPUT_PATH.open("r", encoding="utf-8") as file:
        source = json.load(file)

    output_features = []

    for feature in source.get("features", []):
        properties = feature.get("properties", {})
        positions = properties.get("positions", [])

        timestamps = []
        speeds = []
        courses = []
        headings = []

        for position in positions:
            timestamps.append(position.get("observed_at"))
            speeds.append(position.get("sog_knots"))
            courses.append(position.get("cog_degrees"))
            headings.append(position.get("heading_degrees"))

        frontend_properties = {
            "mmsi": str(properties.get("mmsi", "")),
            "timestamps_utc": timestamps,
            "speed_knots": speeds,
            "course_degrees": courses,
            "heading_degrees": headings,
            "position_count": len(positions),
            "track_start_utc": properties.get("track_start_time"),
            "track_end_utc": properties.get("track_end_time"),
            "ais_completeness": properties.get("ais_completeness"),
            "track_continuity": properties.get("track_continuity"),
            "gap_count": properties.get("gap_count"),
            "max_gap_seconds": properties.get("max_gap_seconds"),
            "source_file": properties.get("source_file"),
            "data_mode": properties.get("data_mode"),
        }

        output_features.append(
            {
                "type": "Feature",
                "geometry": feature.get("geometry"),
                "properties": frontend_properties,
            }
        )

    output = {
        "type": "FeatureCollection",
        "features": output_features,
        "metadata": {
            "source": source.get("metadata", {}).get("source"),
            "crs": source.get("metadata", {}).get("crs"),
            "coordinate_order": source.get("metadata", {}).get("coordinate_order"),
            "start_utc": source.get("metadata", {}).get("start_utc"),
            "end_utc": source.get("metadata", {}).get("end_utc"),
            "candidate_ranking_enabled": source.get("metadata", {}).get(
                "candidate_ranking_enabled"
            ),
            "compatibility_state": source.get("metadata", {}).get(
                "compatibility_state"
            ),
            "limitation": source.get("metadata", {}).get("limitation"),
        },
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print(f"Written: {OUTPUT_PATH}")
    print(f"Features: {len(output_features)}")


if __name__ == "__main__":
    build_frontend_payload()