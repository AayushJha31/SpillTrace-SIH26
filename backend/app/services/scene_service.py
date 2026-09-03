from app.schemas.contracts import SARSceneMetadata, CompatibilityStatus


SCENE_STORE = {
    "scene_demo_001": SARSceneMetadata(
        scene_id="scene_demo_001",
        source="Sentinel-1",
        acquisition_start_utc="2026-09-01T00:00:00Z",
        acquisition_end_utc="2026-09-01T00:10:00Z",
        source_crs="EPSG:4326",
        output_crs="EPSG:4326",
        georeferencing_method="gcp",
        georeferencing_confidence="medium",
    )
}


def list_scenes():
    return list(SCENE_STORE.values())


def get_scene(scene_id: str):
    return SCENE_STORE.get(scene_id)


def get_manifest(scene_id: str):
    scene = get_scene(scene_id)
    if not scene:
        return None
    return {
        "scene_id": scene.scene_id,
        "source": scene.source,
        "available_artifacts": [],
        "notes": "Initial manifest placeholder"
    }


def check_compatibility(scene_id: str):
    scene = get_scene(scene_id)
    if not scene:
        return None
    return CompatibilityStatus(
        compatible=False,
        reasons=["Compatibility inputs not fully integrated yet"],
        temporal_overlap=None,
        geographic_overlap=None,
        crs_valid=True,
        environmental_coverage=None,
    )