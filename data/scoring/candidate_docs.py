from __future__ import annotations

from data.scoring.candidate_config import (
    FEATURE_DESCRIPTIONS,
    SCORING_VERSION,
    UNCERTAINTY_DESCRIPTION,
)
from data.scoring.candidate_scoring import WEIGHTS


def generate_scoring_docs() -> str:
    lines = [
        "# Candidate scoring model",
        "",
        f"Current scoring version: `{SCORING_VERSION}`",
        "",
        "## Features",
        "",
    ]

    for feature, description in FEATURE_DESCRIPTIONS.items():
        weight = WEIGHTS.get(feature, 0.0)
        lines.append(f"- `{feature}` (weight={weight:.2f}): {description}")

    lines.extend(
        [
            "",
            "## Uncertainty",
            "",
            UNCERTAINTY_DESCRIPTION,
            "",
        ]
    )

    return "\n".join(lines)