from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class DriftParametersRequest(BaseModel):
    wind_speed_mps: float = Field(ge=0)
    wind_direction_from_deg: float = Field(ge=0, lt=360)
    current_speed_mps: float = Field(ge=0)
    current_direction_to_deg: float = Field(ge=0, lt=360)

    timestep_minutes: int = Field(default=60, ge=1, le=1440)
    duration_hours: int = Field(default=24, ge=1, le=720)

    wind_drift_coefficient: float = Field(
        default=0.03,
        ge=0,
        le=1,
    )

    current_coefficient: float = Field(
        default=1.0,
        ge=0,
        le=10,
    )

    particle_count: int = Field(
        default=100,
        ge=1,
        le=5000,
    )

    diffusion_mps: float = Field(
        default=25.0,
        ge=0,
        le=10000,
    )

    random_seed: int = Field(default=42)

    mode: Literal[
        "data_backed",
        "analyst_parameter_driven",
    ] = "analyst_parameter_driven"

    vector_source: str = Field(
        default="analyst_input",
        min_length=1,
        max_length=200,
    )

    @field_validator(
        "wind_direction_from_deg",
        "current_direction_to_deg",
    )
    @classmethod
    def normalize_degrees(cls, value: float) -> float:
        return value % 360


class DriftRequest(BaseModel):
    spill_id: str | None = None
    acquisition_time_utc: str | None = None
    slick_geojson: dict[str, Any]
    parameters: DriftParametersRequest


class DriftResponse(BaseModel):
    run_id: str
    run_type: Literal["forecast", "hindcast"]
    status: str
    data_mode: str
    data_mode_label: str
    parameters: dict[str, Any]
    reverse: bool
    start_time_utc: str
    end_time_utc: str
    timestep_minutes: int
    duration_hours: int
    particle_count: int
    step_count: int
    velocity_mps: dict[str, float]
    uncertainty_radius_m: float
    particles: dict[str, Any]
    corridor: dict[str, Any]
    endpoint: dict[str, Any] | None
    assumptions: list[str]