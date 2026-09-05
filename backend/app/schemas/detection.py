from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

CLASS_MAPPING = {
    "0": "sea_surface",
    "1": "oil_spill",
    "2": "look_alike",
    "3": "ship",
    "4": "land",
}

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DetectionRequest(BaseModel):
    scene_id: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1)

class ArtifactRefs(BaseModel):
    oil_mask: str | None = None
    probability_map: str | None = None
    geojson: str | None = None
    metadata_path: str | None = None

class DetectionMetadata(BaseModel):
    detector_name: str = "SpillTrace DeepLabV3+ Engine"
    model_name: str = "ResNet-50 DeepLabV3+"
    checkpoint: str = "oil_spill_seg_resnet_50_deeplab_v3+_80.pt"
    class_mapping: dict[str, str] = CLASS_MAPPING
    oil_class_index: int = 1
    probability_threshold: float = 0.30
    output_crs: str = "EPSG:4326"
    fallback_used: bool = False
    fallback_reason: str | None = None
    total_slicks_detected: int | None = None
    pixel_count_after_cleanup: int | None = None
    centroid: list[float] | None = None
    extra: dict[str, Any] | None = None

class DetectionError(BaseModel):
    code: str
    message: str

class DetectionResponse(BaseModel):
    job_id: UUID
    scene_id: str
    status: JobStatus
    message: str
    artifacts: ArtifactRefs | None = None
    metadata: DetectionMetadata | None = None
    error: DetectionError | None = None
    created_at: datetime
    updated_at: datetime