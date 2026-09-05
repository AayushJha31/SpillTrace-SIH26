from __future__ import annotations

from fastapi import APIRouter

from app.schemas.candidate import (
    CandidateDetailResponse,
    CandidateRunRequest,
    CandidateRunResponse,
)
from app.services.candidate_service import (
    get_candidate_detail,
    get_candidate_run,
    rank_candidates,
)

router = APIRouter(prefix="/api/v1", tags=["candidates"])

@router.post(
    "/spills/{spill_id}/candidates/rank",
    response_model=CandidateRunResponse,
    responses={409: {"description": "Compatibility gate blocked attribution"}},
)
def rank_spill_candidates(
    spill_id: str,
    request: CandidateRunRequest,
) -> CandidateRunResponse:
    return rank_candidates(spill_id, request)

@router.get(
    "/spills/{spill_id}/candidate-runs/{run_id}",
    response_model=CandidateRunResponse,
)
def read_candidate_run(
    spill_id: str,
    run_id: str,
) -> CandidateRunResponse:
    return get_candidate_run(spill_id, run_id)

@router.get(
    "/spills/{spill_id}/candidate-runs/{run_id}/candidates/{candidate_id}",
    response_model=CandidateDetailResponse,
)
def read_candidate_detail(
    spill_id: str,
    run_id: str,
    candidate_id: str,
) -> CandidateDetailResponse:
    return get_candidate_detail(spill_id, run_id, candidate_id)