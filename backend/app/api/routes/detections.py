from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas.detection import (
    ArtifactRefs,
    DetectionError,
    DetectionMetadata,
    DetectionRequest,
    DetectionResponse,
    JobStatus,
)
from app.services.detector_service import detector_service
from app.services.detection_store import detection_store

router = APIRouter(prefix="/detections", tags=["detections"])


@router.post("", response_model=DetectionResponse, status_code=status.HTTP_200_OK)
def create_detection(request: DetectionRequest):
    now = datetime.now(timezone.utc)
    job_id = uuid4()

    queued_job = DetectionResponse(
        job_id=job_id,
        scene_id=request.scene_id,
        status=JobStatus.QUEUED,
        message="Detection job queued.",
        artifacts=None,
        metadata=None,
        error=None,
        created_at=now,
        updated_at=now,
    )
    detection_store.save(queued_job)

    processing_job = detection_store.update(
        job_id,
        status=JobStatus.PROCESSING,
        message="Detection in progress.",
    )
    if processing_job is None:
        raise HTTPException(status_code=500, detail="Could not update job state.")

    try:
        raw = detector_service.run(
            file_path=request.file_path,
            scene_id=request.scene_id,
        )
        normalized = detector_service.normalize(raw)

        final_job = DetectionResponse(
            job_id=job_id,
            scene_id=request.scene_id,
            status=JobStatus(normalized["status"]),
            message=normalized["message"],
            artifacts=ArtifactRefs(**normalized["artifacts"]),
            metadata=DetectionMetadata(**normalized["metadata"]),
            error=None,
            created_at=queued_job.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        detection_store.save(final_job)
        return final_job

    except ValueError as exc:
        code, message = exc.args[0] if exc.args else ("ERR_INVALID_FILE", "Invalid file input.")
    except RuntimeError as exc:
        code, message = exc.args[0] if exc.args else ("ERR_DETECTOR_FAILURE", "Detector execution failed.")
    except Exception:
        code, message = ("ERR_DETECTOR_FAILURE", "Unexpected detector failure.")

    failed_job = DetectionResponse(
        job_id=job_id,
        scene_id=request.scene_id,
        status=JobStatus.FAILED,
        message=message,
        artifacts=None,
        metadata=None,
        error=DetectionError(code=code, message=message),
        created_at=queued_job.created_at,
        updated_at=datetime.now(timezone.utc),
    )
    detection_store.save(failed_job)

    return JSONResponse(
        status_code=500,
        content=failed_job.model_dump(mode="json"),
    )


@router.get("/{job_id}", response_model=DetectionResponse, status_code=status.HTTP_200_OK)
def get_detection(job_id: str):
    job = detection_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Detection job not found.")
    return job