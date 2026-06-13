"""
FastAPI Application
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.video_lab.router import router as video_lab_router


# Ensure runtime directory exists
RUNTIME_BASE = Path("runtime/video_lab/experiments")
RUNTIME_BASE.mkdir(parents=True, exist_ok=True)


app = FastAPI(
    title="Video Capability Lab",
    description="视频生成能力验证平台",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount runtime directory for static file access
app.mount("/runtime", StaticFiles(directory="runtime"), name="runtime")

# Routers
app.include_router(video_lab_router)


@app.get("/")
def root():
    return {
        "name": "Video Capability Lab",
        "version": "0.2.0",
        "description": "视频生成能力验证平台",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
