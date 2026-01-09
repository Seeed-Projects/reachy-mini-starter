"""
FastAPI backend for YOLO object tracking web application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import threading

from .tracking_manager import TrackingManager


# Pydantic models for request validation
class PitchParams(BaseModel):
    p: Optional[float] = None
    i: Optional[float] = None
    d: Optional[float] = None
    gain: Optional[float] = None


class YawParams(BaseModel):
    p: Optional[float] = None
    i: Optional[float] = None
    d: Optional[float] = None
    gain: Optional[float] = None


class DetectorSettings(BaseModel):
    target_class: Optional[str] = None
    conf_threshold: Optional[float] = None


class FilterSettings(BaseModel):
    window_size: Optional[int] = None
    jump_threshold: Optional[int] = None


# Create FastAPI app
app = FastAPI(title="YOLO Object Tracking API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global tracking manager instance
tracking_manager = None
manager_lock = threading.Lock()
initializing = False


def get_manager():
    """Get or create tracking manager"""
    global tracking_manager, initializing
    with manager_lock:
        if tracking_manager is None and not initializing:
            initializing = True
            tracking_manager = TrackingManager()
            initializing = False
        return tracking_manager


def is_ready():
    """Check if manager is initialized and ready"""
    global tracking_manager
    with manager_lock:
        return tracking_manager is not None and tracking_manager.is_initialized


# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    ready = is_ready()
    return {
        "message": "YOLO Object Tracking API",
        "version": "1.0.0",
        "status": "ready" if ready else "initializing",
        "endpoints": {
            "info": "/info",
            "classes": "/classes",
            "params": "/params",
            "control": "/control",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - wait for initialization"""
    if not is_ready():
        return {
            "status": "initializing",
            "message": "Tracking manager is initializing..."
        }
    return {
        "status": "ready",
        "message": "Tracking manager is ready"
    }


@app.get("/info")
async def get_info():
    """Get current tracking information"""
    manager = get_manager()
    return manager.get_info()


@app.get("/classes")
async def get_classes():
    """Get available YOLO classes"""
    manager = get_manager()
    return {"classes": manager.get_available_classes()}


@app.get("/params")
async def get_params():
    """Get current parameters"""
    manager = get_manager()
    return manager.get_params()


@app.post("/control/start")
async def start_tracking():
    """Start tracking"""
    manager = get_manager()
    success = manager.start()
    return {"success": success, "message": "Tracking started" if success else "Already running"}


@app.post("/control/stop")
async def stop_tracking():
    """Stop tracking"""
    manager = get_manager()
    manager.stop()
    return {"success": True, "message": "Tracking stopped"}


@app.post("/control/reset")
async def reset_tracking():
    """Reset tracking state"""
    manager = get_manager()
    manager.reset_tracking()
    return {"success": True, "message": "Tracking reset"}


@app.post("/params/pitch")
async def update_pitch_params(params: PitchParams):
    """Update pitch controller parameters"""
    manager = get_manager()
    manager.update_pitch_params(
        p=params.p,
        i=params.i,
        d=params.d,
        gain=params.gain
    )
    return {"success": True, "message": "Pitch parameters updated"}


@app.post("/params/yaw")
async def update_yaw_params(params: YawParams):
    """Update yaw controller parameters"""
    manager = get_manager()
    manager.update_yaw_params(
        p=params.p,
        i=params.i,
        d=params.d,
        gain=params.gain
    )
    return {"success": True, "message": "Yaw parameters updated"}


@app.post("/params/detector")
async def update_detector_settings(settings: DetectorSettings):
    """Update detector settings"""
    manager = get_manager()
    manager.update_detector_settings(
        target_class=settings.target_class,
        conf_threshold=settings.conf_threshold
    )
    return {"success": True, "message": "Detector settings updated"}


@app.post("/params/filter")
async def update_filter_settings(settings: FilterSettings):
    """Update filter settings"""
    manager = get_manager()
    manager.update_filter_settings(
        window_size=settings.window_size,
        jump_threshold=settings.jump_threshold
    )
    return {"success": True, "message": "Filter settings updated"}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global tracking_manager
    with manager_lock:
        if tracking_manager:
            tracking_manager.cleanup()
            tracking_manager = None


def run_server(host="0.0.0.0", port=8000):
    """Run the API server"""
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
