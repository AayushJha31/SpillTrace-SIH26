from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.detector_service import detector_service

client = TestClient(app)

def test_detection_success(monkeypatch, tmp_path):
    tif = tmp_path / "test_scene.tiff"
    tif.write_text("fake")

    def fake_run(file_path: str, scene_id: str):
        return {
            "status": "COMPLETED",
            "message": "Oil slick detected successfully.",
            "artifacts": {
                "oil_mask": "/storage/outputs/oil_mask.png",
                "probability_map": "/storage/outputs/prob_heatmap.png",
                "geojson": "/storage/outputs/slick_geometry.geojson",
            },
            "metadata": {
                "detector_name": "SpillTrace DeepLabV3+ Engine",
                "model_name": "ResNet-50 DeepLabV3+",
                "checkpoint": "oil_spill_seg_resnet_50_deeplab_v3+_80.pt",
                "fallback_used": False,
                "probability_threshold": 0.30,
                "output_crs": "EPSG:4326",
                "oil_class_index": 1,
            },
        }

    monkeypatch.setattr(detector_service, "run", fake_run)

    response = client.post(
        "/api/v1/detections",
        json={"scene_id": "SAR_20260901_001", "file_path": str(tif)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["metadata"]["oil_class_index"] == 1
    assert body["metadata"]["output_crs"] == "EPSG:4326"

def test_detection_no_oil_completed(monkeypatch, tmp_path):
    tif = tmp_path / "test_scene.tiff"
    tif.write_text("fake")

    def fake_run(file_path: str, scene_id: str):
        return {
            "status": "COMPLETED",
            "message": "Processing successful. No oil pixels detected.",
            "artifacts": {
                "geojson": None,
            },
            "metadata": {
                "fallback_used": False,
                "total_slicks_detected": 0,
            },
        }

    monkeypatch.setattr(detector_service, "run", fake_run)

    response = client.post(
        "/api/v1/detections",
        json={"scene_id": "SAR_20260901_002", "file_path": str(tif)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["metadata"]["total_slicks_detected"] == 0


def test_detection_fallback_completed(monkeypatch, tmp_path):
    tif = tmp_path / "test_scene.tiff"
    tif.write_text("fake")

    def fake_run(file_path: str, scene_id: str):
        return {
            "status": "COMPLETED",
            "message": "Completed using adaptive-threshold fallback.",
            "metadata": {
                "fallback_used": True,
                "fallback_reason": "Checkpoint load failed",
            },
        }

    monkeypatch.setattr(detector_service, "run", fake_run)

    response = client.post(
        "/api/v1/detections",
        json={"scene_id": "SAR_20260901_003", "file_path": str(tif)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["metadata"]["fallback_used"] is True


def test_detection_missing_file():
    response = client.post(
        "/api/v1/detections",
        json={"scene_id": "SAR_20260901_004", "file_path": "/tmp/missing_scene.tiff"},
    )

    assert response.status_code == 500