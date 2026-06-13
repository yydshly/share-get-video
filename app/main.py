"""
FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.video_lab.router import router as video_lab_router


app = FastAPI(
    title="Video Capability Lab",
    description="视频生成能力验证平台",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(video_lab_router)


@app.get("/")
def root():
    return {
        "name": "Video Capability Lab",
        "version": "0.1.0",
        "description": "视频生成能力验证平台",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
