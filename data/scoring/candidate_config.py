from __future__ import annotations

SCORING_VERSION = "v1.0"


FEATURE_DESCRIPTIONS = {
    "spatial_proximity_score": (
        "How close the candidate track is to the SAR polygon centroid."
    ),
    "temporal_overlap_score": (
        "How well the candidate track time window overlaps the spill time window."
    ),
    "heading_compatibility_score": (
        "How consistent the candidate heading is with the drift direction."
    ),
    "route_intersection_score": (
        "Whether the candidate route intersects the drift corridor."
    ),
    "track_continuity_score": (
        "How continuous and plausible the candidate track is over time."
    ),
    "ais_completeness": (
        "How complete the AIS coverage is for the candidate track."
    ),
}


UNCERTAINTY_DESCRIPTION = (
    "Higher values indicate greater uncertainty in the candidate ranking."
)