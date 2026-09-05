from fastapi import APIRouter

from app.api.routes import system
from app.api.routes.detections import router as detections_router

api_router = APIRouter()

api_router.include_router(system.router, tags=["system"])
api_router.include_router(detections_router, tags=["detections"])