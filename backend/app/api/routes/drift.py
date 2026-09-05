from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.drift import DriftRequest, DriftResponse
from app.services.drift_engine import (
    DriftParameters,
    simulate_drift,
)

router = APIRouter(
    prefix="/api/drift",
    tags=["drift"],
)


def _run_drift(
    request: DriftRequest,
    reverse: bool,
) -> DriftResponse:
    try:
        params = DriftParameters(
            **request.parameters.model_dump()
        )

        result = simulate_drift(
            slick_geojson=request.slick_geojson,
            params=params,
            acquisition_time_utc=request.acquisition_time_utc,
            reverse=reverse,
        )

        if request.spill_id:
            result["spill_id"] = request.spill_id

        return DriftResponse.model_validate(result)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drift simulation failed: {exc}",
        ) from exc


@router.post(
    "/forecast",
    response_model=DriftResponse,
)
def forecast(request: DriftRequest) -> DriftResponse:
    return _run_drift(request, reverse=False)


@router.post(
    "/hindcast",
    response_model=DriftResponse,
)
def hindcast(request: DriftRequest) -> DriftResponse:
    return _run_drift(request, reverse=True)