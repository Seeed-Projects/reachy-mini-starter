"""
YOLO Object Tracking Web Application - Main Entry Point

This is a web-based version of the YOLO object tracking system for Reachy Mini.
It provides a modern web interface for real-time tracking control and parameter adjustment.

Usage:
    python main.py

The web interface will be available at:
    - Frontend: http://localhost:8123
    - API Docs: http://localhost:8123/docs
    - Video Stream: http://localhost:8123/video

Dependencies:
    pip install reachy-mini opencv-python ultralytics fastapi uvicorn
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
import uvicorn
import os

from backend.api import app as api_app
from backend.tracking_manager import TrackingManager


# Global tracking manager for video streaming
tracking_manager = None


def get_tracking_manager():
    """Get or create tracking manager"""
    global tracking_manager
    if tracking_manager is None:
        print("Initializing TrackingManager...")
        tracking_manager = TrackingManager()
    return tracking_manager


# Create main FastAPI app
app = FastAPI(title="YOLO Object Tracking Web")


# Startup event - initialize tracking manager
@app.on_event("startup")
async def startup_event():
    """Initialize tracking manager on startup"""
    get_tracking_manager()
    print("TrackingManager ready!")

# Mount API routes
app.mount("/api", api_app)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "frontend", "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates_dir = os.path.join(os.path.dirname(__file__), "frontend", "templates")
templates = Jinja2Templates(directory=templates_dir)


@app.get("/")
async def root(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/video")
async def video_stream():
    """Video streaming endpoint (direct, not under /api)"""
    manager = get_tracking_manager()

    def generate():
        while True:
            frame = manager.get_frame_jpeg()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("YOLO Object Tracking Web Application")
    print("=" * 60)
    print()
    print("Starting server...")
    print()
    print("Web Interface: http://localhost:8123")
    print("API Docs:      http://localhost:8123/docs")
    print("Video Stream:  http://localhost:8123/video")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    uvicorn.run(app, host="0.0.0.0", port=8123, log_level="info")
