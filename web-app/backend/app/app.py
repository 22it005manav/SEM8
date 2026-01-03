"""
Single-file entrypoint to run the Video Dehazing API.

Usage (Windows):
    python app.py
"""

from app.main import app
from app.core.config import settings

if __name__ == "__main__":
    import uvicorn

    # Run FastAPI using a single-file entrypoint
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
