#!/usr/bin/env python
"""
Quick start script for YOLO Object Tracking Web Application
"""

import sys
import subprocess

def main():
    print("=" * 60)
    print("YOLO Object Tracking Web - Quick Start")
    print("=" * 60)
    print()

    # Check if required packages are installed
    required = ['fastapi', 'uvicorn', 'reachy_mini', 'ultralytics', 'cv2']
    missing = []

    for package in required:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'reachy_mini':
                import reachy_mini_sdk
            else:
                __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print("Missing packages:", ", ".join(missing))
        print()
        print("Please install requirements first:")
        print("  pip install -r requirements.txt")
        print()
        return 1

    print("All dependencies are installed!")
    print()
    print("Starting web server...")
    print()
    print("Access the web interface at:")
    print("  → http://localhost:8000")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Run the main application
    from main import app
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

    return 0


if __name__ == "__main__":
    sys.exit(main())
