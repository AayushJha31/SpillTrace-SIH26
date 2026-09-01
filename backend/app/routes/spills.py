from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..schemas import SpillGeometry, SpillMetadataResponse, SpillResponse, SpillUploadResponse

router = APIRouter(prefix="/api/spills", tags=["spills"])

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data" / "sar"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SPILL_STORE: dict[str, dict] = {}


@router.post("/upload", response_model=SpillUploadResponse)
async def upload_spill(file: UploadFile = File(...)):
    spill_id = str(uuid4())
    uploaded_at = datetime.now(timezone.utc)

    original_name = file.filename or f"{spill_id}.bin"
    stored_name = f"{spill_id}_{original_name}"
    stored_path = DATA_DIR / stored_name

    content = await file.read()
    stored_path.write_bytes(content)

    SPILL_STORE[spill_id] = {
        "spill_id": spill_id,
        "filename": original_name,
        "content_type": file.content_type or "application/octet-stream",
        "saved_path": str(stored_path),
        "uploaded_at": uploaded_at,
        "status": "uploaded",
        "source": "manual-upload",
    }

    return SpillUploadResponse(**SPILL_STORE[spill_id])


@router.post("/{spill_id}/detect", response_model=SpillResponse)
async def detect_spill(spill_id: str):
    spill = SPILL_STORE.get(spill_id)
    if not spill:
        raise HTTPException(status_code=404, detail="Spill not found")

    spill["status"] = "detected"

    geometry = SpillGeometry(
        type="Polygon",
        coordinates=[
            [
                [72.810, 18.920],
                [72.845, 18.920],
                [72.845, 18.955],
                [72.810, 18.955],
                [72.810, 18.920],
            ]
        ],
    )

    return SpillResponse(
        spill_id=spill_id,
        status="detected",
        message="Mock segmentation completed successfully",
        geometry=geometry,
        area_sq_km=3.42,
        detected_at=datetime.now(timezone.utc),
    )


@router.get("/{spill_id}", response_model=SpillMetadataResponse)
async def get_spill(spill_id: str):
    spill = SPILL_STORE.get(spill_id)
    if not spill:
        raise HTTPException(status_code=404, detail="Spill not found")

    return SpillMetadataResponse(**spill)