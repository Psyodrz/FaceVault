"""
FaceVault - Main FastAPI Application
Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from database.database import init_db, SessionLocal
from backend.auth import init_default_users
from backend.face_engine import FaceEngine
from backend.liveness_engine import LivenessEngine
from backend.anonymizer_engine import AnonymizerEngine
from backend.analysis_engine import AnalysisEngine
from backend.routes.api import router, set_engines

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize engines and database on startup."""
    print("\n" + "=" * 50)
    print("  FaceVault — Starting Up")
    print("=" * 50)

    # Initialize database and default users
    init_db()
    db = SessionLocal()
    try:
        init_default_users(db)
    finally:
        db.close()

    # Initialize engines
    face_engine = FaceEngine()
    liveness_engine = LivenessEngine()
    anonymizer_engine = AnonymizerEngine()
    analysis_engine = AnalysisEngine()

    # Wire engines into routes
    set_engines(face_engine, liveness_engine, anonymizer_engine, analysis_engine)

    print("=" * 50)
    print("  FaceVault — Ready at http://localhost:8000")
    print("=" * 50 + "\n")

    yield

    print("\n[FaceVault] Shutting down...")


app = FastAPI(
    title="FaceVault",
    description="Face Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router)

# Serve frontend static files (Vite build output)
frontend_dist = os.path.join(BASE_DIR, "frontend", "dist")
frontend_assets = os.path.join(frontend_dist, "assets")

if os.path.exists(frontend_dist):
    if os.path.exists(frontend_assets):
        app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        # Don't intercept API or WebSocket routes
        if path.startswith("api/") or path.startswith("ws/"):
            return
        file_path = os.path.join(frontend_dist, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        # SPA fallback — all routes serve index.html
        return FileResponse(os.path.join(frontend_dist, "index.html"))

