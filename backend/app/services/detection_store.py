from datetime import datetime, timezone
from uuid import UUID

from app.schemas.detection import DetectionResponse

class DetectionStore:
    def __init__(self) -> None:
        self._jobs: dict[str, DetectionResponse] = {}

    def save(self, job: DetectionResponse) -> DetectionResponse:
        self._jobs[str(job.job_id)] = job
        return job

    def get(self, job_id: UUID | str) -> DetectionResponse | None:
        return self._jobs.get(str(job_id))

    def update(self, job_id: UUID | str, **kwargs) -> DetectionResponse | None:
        existing = self.get(job_id)
        if not existing:
            return None

        updated = existing.model_copy(
            update={
                **kwargs,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._jobs[str(updated.job_id)] = updated
        return updated

detection_store = DetectionStore()