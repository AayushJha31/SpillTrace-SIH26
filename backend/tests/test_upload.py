from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_spill_file():
    response = client.post(
        "/api/spills/upload",
        files={"file": ("sample.tif", b"fake-sar-bytes", "image/tiff")},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["filename"] == "sample.tif"
    assert data["content_type"] == "image/tiff"
    assert data["status"] == "uploaded"
    assert "spill_id" in data