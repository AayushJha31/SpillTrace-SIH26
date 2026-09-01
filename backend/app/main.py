from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.spills import router as spills_router

app = FastAPI(title="SpillTrace Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spills_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "spilltrace-backend",
    }