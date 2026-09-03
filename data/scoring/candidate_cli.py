from __future__ import annotations

from data.scoring.candidate_docs import generate_scoring_docs
from data.scoring.candidate_health import check_candidate_scoring_health


def print_scoring_docs() -> None:
    print(generate_scoring_docs())


def print_health_status() -> None:
    result = check_candidate_scoring_health()
    print(f"Status: {result['status']}")
    if "scoring_version" in result:
        print(f"Scoring version: {result['scoring_version']}")
    if result.get("errors"):
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")