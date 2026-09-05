from __future__ import annotations

import math
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import numpy as np
from pyproj import Geod
from shapely.geometry import shape
from shapely.ops import unary_union

geod = Geod(ellps="WGS84")

DriftMode = Literal[
    "data_backed",
    "analyst_parameter_driven",
]


@dataclass
class DriftParameters:
    wind_speed_mps: float
    wind_direction_from_deg: float
    current_speed_mps: float
    current_direction_to_deg: float
    timestep_minutes: int = 60
    duration_hours: int = 24
    wind_drift_coefficient: float = 0.03
    current_coefficient: float = 1.0
    particle_count: int = 100
    diffusion_mps: float = 25.0
    random_seed: int = 42
    mode: DriftMode = "analyst_parameter_driven"
    vector_source: str = "analyst_input"


@dataclass
class DriftPoint:
    particle_id: int
    timestamp_utc: str
    longitude: float
    latitude: float
    step_index: int


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: str | None) -> datetime:
    if not value:
        return _utc_now()

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _meteorological_wind_vector(
    speed_mps: float,
    direction_from_deg: float,
) -> tuple[float, float]:
    """
    Meteorological direction is FROM.
    Convert to movement direction TO, then return east/north components.
    """
    direction_to_rad = math.radians((direction_from_deg + 180.0) % 360.0)
    east = speed_mps * math.sin(direction_to_rad)
    north = speed_mps * math.cos(direction_to_rad)
    return east, north


def _current_vector(
    speed_mps: float,
    direction_to_deg: float,
) -> tuple[float, float]:
    """
    Current direction is TO.
    """
    direction_rad = math.radians(direction_to_deg)
    east = speed_mps * math.sin(direction_rad)
    north = speed_mps * math.cos(direction_rad)
    return east, north


def _combined_velocity(
    params: DriftParameters,
    reverse: bool = False,
) -> tuple[float, float]:
    wind_east, wind_north = _meteorological_wind_vector(
        params.wind_speed_mps,
        params.wind_direction_from_deg,
    )

    current_east, current_north = _current_vector(
        params.current_speed_mps,
        params.current_direction_to_deg,
    )

    east = (
        params.wind_drift_coefficient * wind_east
        + params.current_coefficient * current_east
    )
    north = (
        params.wind_drift_coefficient * wind_north
        + params.current_coefficient * current_north
    )

    if reverse:
        east *= -1.0
        north *= -1.0

    return east, north


def _move_point(
    longitude: float,
    latitude: float,
    east_m: float,
    north_m: float,
) -> tuple[float, float]:
    distance_m = math.hypot(east_m, north_m)

    if distance_m == 0:
        return longitude, latitude

    azimuth_deg = math.degrees(math.atan2(east_m, north_m))
    new_lon, new_lat, _ = geod.fwd(
        longitude,
        latitude,
        azimuth_deg,
        distance_m,
    )

    return float(new_lon), float(new_lat)


def _extract_seed_points(
    slick_geojson: dict[str, Any],
) -> list[tuple[float, float]]:
    geometry_items: list[Any] = []

    if slick_geojson.get("type") == "FeatureCollection":
        for feature in slick_geojson.get("features", []):
            geometry = feature.get("geometry")
            if geometry:
                geometry_items.append(shape(geometry))

    elif slick_geojson.get("type") == "Feature":
        geometry = slick_geojson.get("geometry")
        if geometry:
            geometry_items.append(shape(geometry))

    elif slick_geojson.get("type"):
        geometry_items.append(shape(slick_geojson))

    if not geometry_items:
        raise ValueError("No valid slick geometry was provided.")

    merged = unary_union(geometry_items)

    if merged.is_empty:
        raise ValueError("Slick geometry is empty.")

    points: list[tuple[float, float]] = []

    if merged.geom_type == "Polygon":
        representative = merged.representative_point()
        points.append((representative.x, representative.y))

    elif merged.geom_type == "MultiPolygon":
        for polygon in merged.geoms:
            representative = polygon.representative_point()
            points.append((representative.x, representative.y))

    else:
        representative = merged.representative_point()
        points.append((representative.x, representative.y))

    return points


def _make_corridor(
    points: list[DriftPoint],
    radius_m: float,
) -> dict[str, Any]:
    """
    Creates a GeoJSON polygon around all drift points.
    Uses local longitude/latitude degree approximations only for the
    display corridor; particle movement itself uses geodesic calculations.
    """
    if not points:
        return {
            "type": "FeatureCollection",
            "features": [],
        }

    longitude_scale = 111_320.0
    latitude = sum(point.latitude for point in points) / len(points)
    latitude_scale = max(1.0, 111_320.0 * math.cos(math.radians(latitude)))

    xy = np.array(
        [
            [
                point.longitude * longitude_scale,
                point.latitude * latitude_scale,
            ]
            for point in points
        ]
    )

    center = xy.mean(axis=0)
    distances = np.linalg.norm(xy - center, axis=1)
    max_distance = float(distances.max()) if len(distances) else 0.0
    total_radius = max_distance + radius_m

    angles = np.linspace(0, 2 * math.pi, 72, endpoint=False)

    ring = []
    for angle in angles:
        x = center[0] + total_radius * math.cos(angle)
        y = center[1] + total_radius * math.sin(angle)

        lon = x / longitude_scale
        lat = y / latitude_scale
        ring.append([float(lon), float(lat)])

    ring.append(ring[0])

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "radius_m": radius_m,
                    "construction": "display_uncertainty_corridor",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [ring],
                },
            }
        ],
    }


def _points_geojson(
    points: list[DriftPoint],
) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "particle_id": point.particle_id,
                    "timestamp_utc": point.timestamp_utc,
                    "step_index": point.step_index,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        point.longitude,
                        point.latitude,
                    ],
                },
            }
            for point in points
        ],
    }


def _centroid_feature(
    points: list[DriftPoint],
    name: str,
) -> dict[str, Any] | None:
    if not points:
        return None

    lon = sum(point.longitude for point in points) / len(points)
    lat = sum(point.latitude for point in points) / len(points)

    return {
        "type": "Feature",
        "properties": {
            "name": name,
            "point_count": len(points),
        },
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat],
        },
    }


def simulate_drift(
    slick_geojson: dict[str, Any],
    params: DriftParameters,
    acquisition_time_utc: str | None = None,
    reverse: bool = False,
) -> dict[str, Any]:
    if params.timestep_minutes <= 0:
        raise ValueError("timestep_minutes must be positive.")

    if params.duration_hours <= 0:
        raise ValueError("duration_hours must be positive.")

    if params.particle_count <= 0:
        raise ValueError("particle_count must be positive.")

    seed_points = _extract_seed_points(slick_geojson)

    total_steps = math.ceil(
        params.duration_hours * 60 / params.timestep_minutes
    )

    start_time = _parse_timestamp(acquisition_time_utc)
    rng = np.random.default_rng(params.random_seed)

    velocity_east, velocity_north = _combined_velocity(
        params,
        reverse=reverse,
    )

    points: list[DriftPoint] = []
    final_points: list[tuple[float, float]] = []

    for particle_id in range(params.particle_count):
        seed_lon, seed_lat = seed_points[
            particle_id % len(seed_points)
        ]

        initial_noise_east = rng.normal(0.0, params.diffusion_mps)
        initial_noise_north = rng.normal(0.0, params.diffusion_mps)

        lon, lat = _move_point(
            seed_lon,
            seed_lat,
            initial_noise_east,
            initial_noise_north,
        )

        for step_index in range(total_steps + 1):
            timestamp = start_time + timedelta(
                minutes=step_index * params.timestep_minutes
            )

            points.append(
                DriftPoint(
                    particle_id=particle_id,
                    timestamp_utc=timestamp.isoformat(),
                    longitude=lon,
                    latitude=lat,
                    step_index=step_index,
                )
            )

            if step_index == total_steps:
                final_points.append((lon, lat))
                continue

            timestep_seconds = params.timestep_minutes * 60

            diffusion_east = rng.normal(
                0.0,
                params.diffusion_mps * math.sqrt(
                    max(1.0, params.timestep_minutes / 60.0)
                ),
            )

            diffusion_north = rng.normal(
                0.0,
                params.diffusion_mps * math.sqrt(
                    max(1.0, params.timestep_minutes / 60.0)
                ),
            )

            east_step = velocity_east * timestep_seconds + diffusion_east
            north_step = velocity_north * timestep_seconds + diffusion_north

            lon, lat = _move_point(
                lon,
                lat,
                east_step,
                north_step,
            )

    endpoint_points = [
        DriftPoint(
            particle_id=index,
            timestamp_utc=start_time.isoformat(),
            longitude=lon,
            latitude=lat,
            step_index=total_steps,
        )
        for index, (lon, lat) in enumerate(final_points)
    ]

    uncertainty_radius_m = max(
        params.diffusion_mps * math.sqrt(max(1, total_steps)),
        params.diffusion_mps,
    )

    all_points_geojson = _points_geojson(points)
    corridor_geojson = _make_corridor(
        points,
        radius_m=uncertainty_radius_m,
    )

    endpoint_geojson = _centroid_feature(
        endpoint_points,
        name="forecast_endpoint" if not reverse else "hindcast_origin",
    )

    run_id = str(uuid.uuid4())

    return {
        "run_id": run_id,
        "run_type": "forecast" if not reverse else "hindcast",
        "status": "COMPLETED",
        "data_mode": params.mode,
        "data_mode_label": (
            "Data-Backed Environmental Mode"
            if params.mode == "data_backed"
            else "Analyst Parameter-Driven Scenario Simulation"
        ),
        "parameters": asdict(params),
        "reverse": reverse,
        "start_time_utc": start_time.isoformat(),
        "end_time_utc": (
            start_time
            + timedelta(minutes=total_steps * params.timestep_minutes)
        ).isoformat(),
        "timestep_minutes": params.timestep_minutes,
        "duration_hours": params.duration_hours,
        "particle_count": params.particle_count,
        "step_count": total_steps + 1,
        "velocity_mps": {
            "east": velocity_east,
            "north": velocity_north,
        },
        "uncertainty_radius_m": uncertainty_radius_m,
        "particles": all_points_geojson,
        "corridor": corridor_geojson,
        "endpoint": endpoint_geojson,
        "assumptions": [
            "Particle motion uses geodesic WGS84 forward calculations.",
            "Wind direction is interpreted as meteorological direction FROM.",
            "Current direction is interpreted as direction TO.",
            "Diffusion represents unresolved environmental uncertainty.",
            "This is not a confirmed pollution-source attribution.",
        ],
    }