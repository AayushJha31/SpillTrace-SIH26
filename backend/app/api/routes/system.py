from fastapi import APIRouter
from app.schemas.common import HealthResponse

router = APIRouter(tags=["system"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse()