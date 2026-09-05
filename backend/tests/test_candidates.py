from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _base_request() -> dict:
    return {
        "compatibility": {
            "compatible": True,
            "status": "passed",
            "temporal_overlap": True,
            "geographic_overlap": True,
            "crs_valid": True,
            "environmental_coverage": True,
            "reasons": [],
        },
        "drift_evidence": {
            "run_id": "hindcast_test_001",
            "run_type": "hindcast",
            "mode": "data_backed",
            "corridor_reference": "origin_corridor_test.geojson",
            "uncertainty_radius_m": 800,
            "assumptions": [],
        },
        "candidates": [
            {
                "candidate_id": "candidate_001",
                "mmsi": "419001234",
                "vessel_name": "TEST VESSEL A",
                "spatial_score": 0.95,
                "temporal_score": 0.90,
                "heading_score": 0.80,
                "intersection_score": 0.90,
                "continuity_score": 0.88,
                "quality_score": 0.92,
                "distance_to_origin_m": 450,
                "minutes_from_origin": 12,
                "intersects_corridor": True,
                "ais_quality": {
                    "track_continuity": 0.88,
                    "data_completeness": 0.92,
                    "position_count": 120,
                    "gap_count": 2,
                    "source": "synthetic_test_fixture",
                },
                "source_reference": "test_fixture_ais.csv",
                "track_reference": "track_001",
            },
            {
                "candidate_id": "candidate_002",
                "mmsi": "419005678",
                "vessel_name": "TEST VESSEL B",
                "spatial_score": 0.30,
                "temporal_score": 0.20,
                "heading_score": 0.40,
                "intersection_score": 0.20,
                "continuity_score": 0.50,
                "quality_score": 0.60,
                "distance_to_origin_m": 5200,
                "minutes_from_origin": 180,
                "intersects_corridor": False,
                "ais_quality": {
                    "track_continuity": 0.50,
                    "data_completeness": 0.60,
                    "position_count": 40,
                    "gap_count": 15,
                    "source": "synthetic_test_fixture",
                },
                "source_reference": "test_fixture_ais.csv",
                "track_reference": "track_002",
            },
        ],
        "limit": 10,
    }


def test_rank_candidates_returns_highest_ranked_candidate():
    response = client.post(
        "/api/v1/spills/spill_test_001/candidates/rank",
        json=_base_request(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "completed"
    assert payload["spill_id"] == "spill_test_001"
    assert len(payload["candidates"]) == 2
    assert payload["candidates"][0]["rank"] == 1
    assert payload["candidates"][0]["mmsi"] == "419001234"
    assert payload["candidates"][0]["label"] == (
        "highest-ranked candidate under available evidence"
    )
    assert "score_contributions" in payload["candidates"][0]
    assert "weighted_contributions" in payload["candidates"][0]
    assert "evidence_statements" in payload["candidates"][0]
    assert payload["disclaimer"] == (
      "This result identifies the highest-ranked candidate under available evidence. "
      "It does not establish a confirmed polluter."
    )


def test_score_weights_sum_to_one():
    response = client.post(
        "/api/v1/spills/spill_test_002/candidates/rank",
        json=_base_request(),
    )

    assert response.status_code == 200

    candidate = response.json()["candidates"][0]
    weighted = candidate["weighted_contributions"]

    total = sum(weighted.values())

    assert 0 <= total <= 1
    assert abs(candidate["score"] - total) < 0.00001


def test_incompatible_data_returns_409():
    request = _base_request()

    request["compatibility"] = {
        "compatible": False,
        "status": "blocked",
        "temporal_overlap": False,
        "geographic_overlap": True,
        "crs_valid": True,
        "environmental_coverage": False,
        "reasons": [
            "AIS time range does not overlap SAR acquisition.",
            "Environmental forcing data is unavailable.",
        ],
    }

    response = client.post(
        "/api/v1/spills/spill_test_003/candidates/rank",
        json=request,
    )

    assert response.status_code == 409
    detail = response.json()["detail"]

    assert detail["code"] == "COMPATIBILITY_FAILED"
    assert detail["details"]["temporal_overlap"] is False
    assert detail["details"]["environmental_coverage"] is False


def test_candidate_detail_endpoint():
    response = client.post(
        "/api/v1/spills/spill_test_004/candidates/rank",
        json=_base_request(),
    )

    assert response.status_code == 200

    payload = response.json()
    run_id = payload["run_id"]
    candidate_id = payload["candidates"][0]["candidate_id"]

    detail_response = client.get(
        f"/api/v1/spills/spill_test_004/"
        f"candidate-runs/{run_id}/candidates/{candidate_id}"
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["spill_id"] == "spill_test_004"
    assert detail["run_id"] == run_id
    assert detail["candidate_id"] == candidate_id
    assert detail["ais_quality"]["source"] == "synthetic_test_fixture"


def test_missing_candidate_detail_returns_404():
    response = client.post(
        "/api/v1/spills/spill_test_005/candidates/rank",
        json=_base_request(),
    )

    assert response.status_code == 200

    run_id = response.json()["run_id"]

    detail_response = client.get(
        f"/api/v1/spills/spill_test_005/"
        f"candidate-runs/{run_id}/candidates/does_not_exist"
    )

    assert detail_response.status_code == 404
    assert detail_response.json()["detail"]["code"] == "CANDIDATE_NOT_FOUND"