from typing import Any
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, Any] | None = None
    run_id: str | None = None

class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "backend"