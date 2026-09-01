from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class SpillUploadRequest(BaseModel):
    filename: str
    content_type: str
    source: Optional[str] = None


class SpillUploadResponse(BaseModel):
    spill_id: str
    filename: str
    content_type: str
    saved_path: str
    uploaded_at: datetime
    status: str


class SpillGeometry(BaseModel):
    type: str
    coordinates: list[Any]


class SpillResponse(BaseModel):
    spill_id: str
    status: str
    message: str
    geometry: Optional[SpillGeometry] = None
    area_sq_km: Optional[float] = None
    detected_at: Optional[datetime] = None


class SpillMetadataResponse(BaseModel):
    spill_id: str
    filename: str
    status: str
    uploaded_at: datetime
    source: Optional[str] = None