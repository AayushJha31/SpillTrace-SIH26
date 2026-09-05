from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.drift import router as drift_router
from app.core.config import settings
from app.api.routes import system, scenes, detections, spills

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": str(exc),
            "details": None,
            "run_id": request.headers.get("x-run-id"),
        },
    )


app.include_router(system.router, prefix=settings.api_prefix)
app.include_router(scenes.router, prefix=settings.api_prefix)
app.include_router(detections.router, prefix=settings.api_prefix)
app.include_router(spills.router, prefix=settings.api_prefix)
app.include_router(drift_router)
app.include_router(detections.router, prefix='/api/v1')
