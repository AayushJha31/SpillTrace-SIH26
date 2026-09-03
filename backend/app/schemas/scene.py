from pydantic import BaseModel
from app.schemas.contracts import SARSceneMetadata, CompatibilityStatus

class SceneSelectionResponse(BaseModel):
    scenes: list[SARSceneMetadata]

class SceneManifestResponse(BaseModel):
    scene: SARSceneMetadata
    manifest: dict

class CompatibilityResponse(BaseModel):
    scene_id: str
    compatibility: CompatibilityStatus