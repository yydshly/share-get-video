"""
FastAPI Application
"""

import os
import sys
from pathlib import Path

# Load .env if not already loaded. Skip during pytest runs so tests
# can control the environment. override=False preserves system env vars.
_in_pytest = "pytest" in sys.modules
if not _in_pytest:
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
    except ImportError:
        pass  # dotenv not installed; assume env is set elsewhere

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.video_lab.router import router as video_lab_router

# Ensure runtime directory exists
from app.video_lab.config import RUNTIME_DIR, VIDEO_LAB_EXPERIMENTS_DIR, PUBLIC_RUNTIME_URL_PREFIX

RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


app = FastAPI(
    title="Video Capability Lab",
    description="视频生成能力验证平台",
    version="1.2.3",
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
app.mount(f"{PUBLIC_RUNTIME_URL_PREFIX}", StaticFiles(directory=str(RUNTIME_DIR)), name="runtime")

# Routers
app.include_router(video_lab_router)


@app.get("/")
def root():
    return {
        "name": "Video Capability Lab",
        "version": app.version,
        "description": "视频生成能力验证平台",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
