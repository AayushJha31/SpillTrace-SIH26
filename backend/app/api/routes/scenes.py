from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_run_id
from app.schemas.scene import (
    SceneSelectionResponse,
    SceneManifestResponse,
    CompatibilityResponse,
)
from app.services.scene_service import list_scenes, get_scene, get_manifest, check_compatibility

router = APIRouter(prefix="/scenes", tags=["scenes"])


@router.get("", response_model=SceneSelectionResponse)
def get_scenes(run_id: str = Depends(get_run_id)):
    return SceneSelectionResponse(scenes=list_scenes())


@router.get("/{scene_id}/manifest", response_model=SceneManifestResponse)
def scene_manifest(scene_id: str, run_id: str = Depends(get_run_id)):
    scene = get_scene(scene_id)
    manifest = get_manifest(scene_id)
    if not scene or not manifest:
        raise HTTPException(status_code=404, detail={
            "error": "scene_not_found",
            "message": f"Scene {scene_id} not found",
            "run_id": run_id
        })
    return SceneManifestResponse(scene=scene, manifest=manifest)


@router.get("/{scene_id}/compatibility", response_model=CompatibilityResponse)
def scene_compatibility(scene_id: str, run_id: str = Depends(get_run_id)):
    compatibility = check_compatibility(scene_id)
    if compatibility is None:
        raise HTTPException(status_code=404, detail={
            "error": "scene_not_found",
            "message": f"Scene {scene_id} not found",
            "run_id": run_id
        })
    return CompatibilityResponse(scene_id=scene_id, compatibility=compatibility)