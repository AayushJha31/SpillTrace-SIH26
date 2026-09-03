from __future__ import annotations

from data.scoring.candidate_health import check_candidate_scoring_health


def test_check_candidate_scoring_health_returns_healthy() -> None:
    result = check_candidate_scoring_health()

    assert result["status"] == "healthy"
    assert result["scoring_version"] == "v1.0"
    assert "errors" not in result or result.get("errors") == []