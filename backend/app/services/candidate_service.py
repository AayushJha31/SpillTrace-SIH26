from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable
from uuid import uuid4

from fastapi import HTTPException, status

from app.schemas.candidate import (
    CandidateDetailResponse,
    CandidateInput,
    CandidateResult,
    CandidateRunRequest,
    CandidateRunResponse,
    CompatibilityStatus,
    DriftEvidence,
    ScoreContributions,
    WeightedScoreContributions,
)


WEIGHTS = {
    "spatial": 0.30,
    "temporal": 0.25,
    "heading": 0.15,
    "intersection": 0.15,
    "continuity": 0.10,
    "quality": 0.05,
}

DISCLAIMER = (
    "This result identifies the highest-ranked candidate under available evidence. "
    "It does not establish a confirmed polluter."
)

_RUNS: dict[str, CandidateRunResponse] = {}
_DETAILS: dict[tuple[str, str], CandidateDetailResponse] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _request_id() -> str:
    return f"req_{uuid4().hex[:16]}"


def _blocked_error(compatibility: CompatibilityStatus) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "COMPATIBILITY_FAILED",
            "message": (
                "Candidate attribution is blocked because the available "
                "AIS, SAR, or environmental data is incompatible."
            ),
            "details": {
                "temporal_overlap": compatibility.temporal_overlap,
                "geographic_overlap": compatibility.geographic_overlap,
                "crs_valid": compatibility.crs_valid,
                "environmental_coverage": compatibility.environmental_coverage,
                "reasons": compatibility.reasons,
            },
            "request_id": _request_id(),
            "timestamp_utc": _utc_now().isoformat(),
        },
    )


def _score(candidate: CandidateInput) -> tuple[float, ScoreContributions]:
    contributions = ScoreContributions(
        spatial=candidate.spatial_score,
        temporal=candidate.temporal_score,
        heading=candidate.heading_score,
        intersection=1.0 if candidate.intersects_corridor else candidate.intersection_score,
        continuity=candidate.continuity_score,
        quality=candidate.quality_score,
    )

    weighted = (
        contributions.spatial * WEIGHTS["spatial"]
        + contributions.temporal * WEIGHTS["temporal"]
        + contributions.heading * WEIGHTS["heading"]
        + contributions.intersection * WEIGHTS["intersection"]
        + contributions.continuity * WEIGHTS["continuity"]
        + contributions.quality * WEIGHTS["quality"]
    )

    return round(weighted, 6), contributions


def _weighted_contributions(
    contributions: ScoreContributions,
) -> WeightedScoreContributions:
    return WeightedScoreContributions(
        spatial=round(contributions.spatial * WEIGHTS["spatial"], 6),
        temporal=round(contributions.temporal * WEIGHTS["temporal"], 6),
        heading=round(contributions.heading * WEIGHTS["heading"], 6),
        intersection=round(contributions.intersection * WEIGHTS["intersection"], 6),
        continuity=round(contributions.continuity * WEIGHTS["continuity"], 6),
        quality=round(contributions.quality * WEIGHTS["quality"], 6),
    )


def _evidence_statements(
    candidate: CandidateInput,
    contributions: ScoreContributions,
    drift: DriftEvidence,
) -> list[str]:
    statements = [
        (
            f"AIS track is {candidate.distance_to_origin_m:.0f} m from the "
            "estimated origin corridor."
        ),
        (
            f"The AIS track is {abs(candidate.minutes_from_origin):.1f} minutes "
            "from the estimated origin time."
        ),
        (
            "The track intersects the drift corridor."
            if candidate.intersects_corridor
            else "The track does not intersect the drift corridor."
        ),
        (
            f"Track continuity is {candidate.ais_quality.track_continuity:.2f} "
            f"with {candidate.ais_quality.position_count} positions."
        ),
        (
            f"Drift evidence comes from {drift.run_type} run {drift.run_id} "
            f"in {drift.mode} mode."
        ),
    ]

    if contributions.temporal < 0.5:
        statements.append("Temporal alignment is weak and should reduce confidence.")
    if contributions.spatial < 0.5:
        statements.append("Spatial proximity is weak and should reduce confidence.")
    if candidate.ais_quality.data_completeness < 0.7:
        statements.append("AIS data completeness is limited.")

    return statements


def _to_result(
    candidate: CandidateInput,
    rank: int,
    drift: DriftEvidence,
) -> CandidateResult:
    score, contributions = _score(candidate)

    return CandidateResult(
        candidate_id=candidate.candidate_id,
        mmsi=candidate.mmsi,
        vessel_name=candidate.vessel_name,
        rank=rank,
        score=score,
        label=(
            "highest-ranked candidate under available evidence"
            if rank == 1
            else "candidate under available evidence"
        ),
        score_contributions=contributions,
        weighted_contributions=_weighted_contributions(contributions),
        ais_quality=candidate.ais_quality,
        drift_evidence=drift,
        evidence_statements=_evidence_statements(candidate, contributions, drift),
        source_reference=candidate.source_reference,
        track_reference=candidate.track_reference,
    )


def _stable_run_id(spill_id: str, candidates: Iterable[CandidateInput]) -> str:
    source = spill_id + "|" + "|".join(
        sorted(f"{candidate.candidate_id}:{candidate.mmsi}" for candidate in candidates)
    )
    digest = sha256(source.encode("utf-8")).hexdigest()[:16]
    return f"candidate_run_{digest}"


def rank_candidates(
    spill_id: str,
    request: CandidateRunRequest,
) -> CandidateRunResponse:
    if not request.compatibility.compatible:
        raise _blocked_error(request.compatibility)

    run_id = _stable_run_id(spill_id, request.candidates)
    now = _utc_now()

    ranked_inputs = sorted(
        request.candidates,
        key=lambda item: _score(item)[0],
        reverse=True,
    )[: request.limit]

    results = [
        _to_result(candidate, rank=index, drift=request.drift_evidence)
        for index, candidate in enumerate(ranked_inputs, start=1)
    ]

    response = CandidateRunResponse(
        run_id=run_id,
        spill_id=spill_id,
        status="completed" if results else "no_candidates",
        compatibility=request.compatibility,
        candidates=results,
        data_mode=request.drift_evidence.mode,
        disclaimer=DISCLAIMER,
        created_at_utc=now,
    )

    _RUNS[(spill_id, run_id)] = response

    for result in results:
        detail = CandidateDetailResponse(
            **result.model_dump(),
            spill_id=spill_id,
            run_id=run_id,
        )
        _DETAILS[(run_id, result.candidate_id)] = detail

    return response


def get_candidate_run(spill_id: str, run_id: str) -> CandidateRunResponse:
    response = _RUNS.get((spill_id, run_id))
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CANDIDATE_RUN_NOT_FOUND",
                "message": "Candidate run was not found.",
                "details": {"spill_id": spill_id, "run_id": run_id},
                "request_id": _request_id(),
                "timestamp_utc": _utc_now().isoformat(),
            },
        )
    return response


def get_candidate_detail(
    spill_id: str,
    run_id: str,
    candidate_id: str,
) -> CandidateDetailResponse:
    response = get_candidate_run(spill_id, run_id)
    detail = _DETAILS.get((run_id, candidate_id))

    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "CANDIDATE_NOT_FOUND",
                "message": "Candidate was not found in this run.",
                "details": {"candidate_id": candidate_id},
                "request_id": _request_id(),
                "timestamp_utc": _utc_now().isoformat(),
            },
        )

    return detail