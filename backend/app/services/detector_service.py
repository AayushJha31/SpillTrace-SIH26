from pathlib import Path
from typing import Any

from app.schemas.detection import CLASS_MAPPING

try:
    from ml.day1_inference import process_sar_scene
except ImportError:
    process_sar_scene = None


class DetectorService:
    def run(self, file_path: str, scene_id: str) -> dict[str, Any]:
        path = Path(file_path)

        if not path.exists():
            raise ValueError(("ERR_INVALID_FILE", "Input file does not exist."))

        if path.suffix.lower() not in {".tif", ".tiff"}:
            raise ValueError(("ERR_INVALID_FILE", "Expected a GeoTIFF input file."))

        if process_sar_scene is None:
            raise RuntimeError(("ERR_DETECTOR_IMPORT", "Could not import process_sar_scene from sar_inference.py."))

        result = process_sar_scene(file_path=str(path), scene_id=scene_id)

        if not isinstance(result, dict):
            raise RuntimeError(("ERR_DETECTOR_RESPONSE", "Detector returned a non-dictionary response."))

        return result

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        artifacts = raw.get("artifacts", {}) or {}
        metadata = artifacts.get("metadata", {}) or raw.get("metadata", {}) or {}

        return {
            "status": str(raw.get("status", "COMPLETED")).upper(),
            "message": raw.get("message", "Detection completed."),
            "artifacts": {
                "oil_mask": artifacts.get("oil_mask") or artifacts.get("final_oil_mask"),
                "probability_map": artifacts.get("probability_map") or artifacts.get("prob_heatmap"),
                "geojson": artifacts.get("geojson") or artifacts.get("slick_geojson"),
                "metadata_path": artifacts.get("metadata_path"),
            },
            "metadata": {
                "detector_name": metadata.get("detector_name", "SpillTrace DeepLabV3+ Engine"),
                "model_name": metadata.get("model_name", "ResNet-50 DeepLabV3+"),
                "checkpoint": metadata.get("checkpoint", "oil_spill_seg_resnet_50_deeplab_v3+_80.pt"),
                "class_mapping": CLASS_MAPPING,
                "oil_class_index": metadata.get("oil_class_index", 1),
                "probability_threshold": metadata.get("probability_threshold", 0.30),
                "output_crs": metadata.get("output_crs", "EPSG:4326"),
                "fallback_used": metadata.get("fallback_used", False),
                "fallback_reason": metadata.get("fallback_reason"),
                "total_slicks_detected": metadata.get("total_slicks_detected"),
                "pixel_count_after_cleanup": metadata.get("pixel_count_after_cleanup"),
                "centroid": metadata.get("centroid"),
                "extra": metadata,
            },
            "error": raw.get("error"),
        }


detector_service = DetectorService()
