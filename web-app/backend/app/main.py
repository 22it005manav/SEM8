"""
FastAPI Application - Video Dehazing Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.core.config import settings
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("=" * 60)
    print("🚀 Video Dehazing Backend + Frontend Starting...")
    print("=" * 60)
    print(f"📁 Upload Directory: {settings.UPLOAD_DIR}")
    print(f"📁 Output Directory: {settings.OUTPUT_DIR}")
    print(f"📁 Model Directory: {settings.MODEL_DIR}")
    print(f"🔧 Device: {settings.DEVICE}")
    print(f"🎯 Default Model: {settings.DEFAULT_MODEL_LAYERS} layers")
    print(f"🌐 Access at: http://localhost:{settings.PORT}")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Video Dehazing API",
    description="Real-time video dehazing using deep learning",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS (minimal needed when serving frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

# Serve static files (for downloads)
app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")

# Serve frontend static files
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dist / "assets")), name="static")
else:
    print("⚠️  Frontend dist not found. Run 'npm run build' in frontend directory")


@app.get("/")
async def root():
    """Serve frontend index.html"""
    from fastapi.responses import FileResponse
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Video Dehazing API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Catch-all to serve frontend files"""
    from fastapi.responses import FileResponse
    from pathlib import Path as PathlibPath
    
    # Try to serve the file directly
    file_path = frontend_dist / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    
    # Otherwise serve index.html for React routing
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    
    return {"error": "File not found"}, 404


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
