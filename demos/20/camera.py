#!/usr/bin/env python3
"""独立的摄像头 MJPEG 流服务.

这个服务可以独立运行，与 Reachy Mini SDK 并行，
通过 HTTP 提供 MJPEG 视频流，跨平台兼容（浏览器原生支持）。

支持 Raspberry Pi Camera (Picamera2) 和 USB 摄像头。

运行方式:
    python camera_stream_service.py

API 端点:
    GET / - 服务状态
    GET /stream - MJPEG 视频流
    GET /snapshot - 单帧 JPEG 快照
    GET /status - 摄像头状态
    GET /info - 摄像头详细信息

使用示例:
    # 浏览器直接访问
    http://10.42.0.75:8002/stream

    # curl 下载快照
    curl http://10.42.0.75:8002/snapshot --output photo.jpg

    # HTML 中使用
    <img src="http://10.42.0.75:8002/stream" />
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

import cv2
import numpy as np
import numpy.typing as npt
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse


# ===== 配置 =====
class Config:
    """服务配置."""

    # API 服务配置
    HOST = "0.0.0.0"
    PORT = 8002  # 使用不同端口避免与其他服务冲突

    # 摄像头配置
    DEFAULT_FPS = 15
    DEFAULT_QUALITY = 85
    MAX_FPS = 30

    # Picamera2 配置
    PICAMERA_WIDTH = 2304
    PICAMERA_HEIGHT = 1296
    PICAMERA_FORMAT = "RGB888"


# ===== 全局状态 =====
camera_backend: Optional[str] = None  # 'picamera2' 或 'opencv'


# ===== 摄像头管理器 =====
class CameraManager:
    """摄像头管理器."""

    def __init__(self):
        self._camera = None  # Picamera2 或 cv2.VideoCapture
        self._backend: Optional[str] = None  # 'picamera2' 或 'opencv'
        self._specs: Optional[dict] = None
        self._last_frame: Optional[npt.NDArray[np.uint8]] = None
        self._last_frame_time: float = 0
        self._width = 0
        self._height = 0

    def initialize(self) -> bool:
        """初始化摄像头."""
        global camera_backend

        if self._camera is not None:
            return True

        # 优先尝试 Picamera2 (Raspberry Pi Camera)
        if self._init_picamera2():
            self._backend = 'picamera2'
            camera_backend = 'picamera2'
            logging.info("Camera initialized: Picamera2")
            return True

        # 回退到 OpenCV (USB 摄像头)
        if self._init_opencv():
            self._backend = 'opencv'
            camera_backend = 'opencv'
            logging.info("Camera initialized: OpenCV (USB)")
            return True

        logging.error("No camera found!")
        return False

    def _init_picamera2(self) -> bool:
        """尝试初始化 Picamera2."""
        try:
            from picamera2 import Picamera2

            logging.info("Trying Picamera2...")
            picam2 = Picamera2()

            # 创建预览配置
            config = picam2.create_preview_configuration(
                main={"size": (Config.PICAMERA_WIDTH, Config.PICAMERA_HEIGHT),
                      "format": Config.PICAMERA_FORMAT}
            )
            picam2.configure(config)
            picam2.start()

            # 等待摄像头准备就绪
            time.sleep(0.5)

            # 测试捕获一帧
            frame = picam2.capture_array()
            if frame is None or frame.size == 0:
                picam2.stop()
                return False

            self._camera = picam2
            self._width = Config.PICAMERA_WIDTH
            self._height = Config.PICAMERA_HEIGHT
            self._specs = {
                "name": "Raspberry Pi Camera",
                "backend": "picamera2",
                "width": self._width,
                "height": self._height,
            }

            logging.info(f"Picamera2: {self._width}x{self._height}")
            return True

        except ImportError:
            logging.warning("Picamera2 not available")
            return False
        except Exception as e:
            logging.warning(f"Picamera2 init failed: {e}")
            return False

    def _init_opencv(self) -> bool:
        """尝试初始化 OpenCV 摄像头."""
        try:
            logging.info("Trying OpenCV...")

            # 尝试打开 /dev/video0
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            if not cap.isOpened():
                # 尝试其他索引
                for i in range(4):
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        break

            if not cap.isOpened():
                return False

            # 设置 MJPEG 格式（减少 CPU 负载）
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

            # 设置分辨率
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

            # 测试读取一帧
            ret, frame = cap.read()
            if not ret or frame is None:
                cap.release()
                return False

            self._camera = cap
            self._width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self._height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # 获取摄像头名称
            backend_name = cap.getBackendName()
            self._specs = {
                "name": "USB Camera",
                "backend": "opencv",
                "backend_name": backend_name,
                "width": self._width,
                "height": self._height,
            }

            logging.info(f"OpenCV: {self._width}x{self._height}, backend: {backend_name}")
            return True

        except Exception as e:
            logging.warning(f"OpenCV init failed: {e}")
            return False

    def get_frame(self) -> Optional[npt.NDArray[np.uint8]]:
        """获取一帧图像 (BGR 格式)."""
        if self._camera is None:
            return None

        try:
            if self._backend == 'picamera2':
                # Picamera2 返回 RGB，需要转换为 BGR
                frame_rgb = self._camera.capture_array()
                if frame_rgb is None or frame_rgb.size == 0:
                    return self._last_frame

                frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                self._last_frame = frame.copy()
                self._last_frame_time = time.time()
                return frame

            else:  # opencv
                ret, frame = self._camera.read()
                if ret and frame is not None:
                    self._last_frame = frame.copy()
                    self._last_frame_time = time.time()
                    return frame
                else:
                    # 使用缓存帧
                    return self._last_frame

        except Exception as e:
            logging.error(f"Error reading frame: {e}")
            return self._last_frame

    def get_resolution(self) -> tuple[int, int]:
        """获取当前分辨率."""
        return (self._width, self._height)

    def get_fps(self) -> float:
        """获取当前帧率."""
        if self._backend == 'opencv' and self._camera is not None:
            return self._camera.get(cv2.CAP_PROP_FPS)
        return 30.0  # Picamera2 默认

    def close(self):
        """关闭摄像头."""
        if self._camera is None:
            return

        try:
            if self._backend == 'picamera2':
                self._camera.stop()
                self._camera.close()
            else:  # opencv
                self._camera.release()

            self._camera = None
            logging.info("Camera closed")

        except Exception as e:
            logging.error(f"Error closing camera: {e}")


# 全局摄像头管理器
camera_manager = CameraManager()


# ===== MJPEG 流生成器 =====
def generate_mjpeg(quality: int = 85, fps: int = 15):
    """生成 MJPEG 流.

    Args:
        quality: JPEG 质量 (1-100)
        fps: 目标帧率

    Yields:
        MJPEG 格式的视频流
    """
    frame_interval = 1.0 / fps

    try:
        while True:
            start_time = time.time()

            # 获取帧
            frame = camera_manager.get_frame()
            if frame is None:
                # 生成空白帧
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(
                    frame,
                    "No Camera Signal",
                    (160, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )

            # 编码为 JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            ret, encoded = cv2.imencode(".jpg", frame, encode_param)
            if not ret:
                continue

            jpeg_bytes = encoded.tobytes()

            # 生成 MJPEG 响应
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(jpeg_bytes)).encode() + b"\r\n\r\n"
            )
            yield jpeg_bytes
            yield b"\r\n"

            # 控制帧率
            elapsed = time.time() - start_time
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)

    except GeneratorExit:
        logging.info("MJPEG stream closed by client")
    except Exception as e:
        logging.error(f"MJPEG stream error: {e}")


# ===== FastAPI 应用 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    # 启动时初始化摄像头
    logging.info("Camera Stream Service starting...")
    if camera_manager.initialize():
        logging.info("Camera initialized successfully")
    else:
        logging.warning("Failed to initialize camera, will return error on requests")

    yield

    # 关闭时清理资源
    logging.info("Camera Stream Service shutting down...")
    camera_manager.close()


app = FastAPI(
    title="Reachy Mini Camera Stream Service",
    description="独立的摄像头 MJPEG 流服务，支持 Picamera2 和 USB 摄像头",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """根路径."""
    return {
        "service": "Reachy Mini Camera Stream Service",
        "version": "1.0.0",
        "status": "running",
        "camera_backend": camera_backend,
        "camera_available": camera_manager._camera is not None,
    }


@app.get("/stream")
async def get_stream(quality: int = 85, fps: int = 15):
    """获取 MJPEG 视频流.

    Args:
        quality: JPEG 质量 (1-100)
        fps: 目标帧率 (1-30)

    Returns:
        StreamingResponse with MJPEG content type

    Examples:
        浏览器访问:
        http://10.42.0.75:8002/stream

        HTML 中使用:
        <img src="http://10.42.0.75:8002/stream" />
    """
    if camera_manager._camera is None:
        raise HTTPException(
            status_code=503, detail="Camera not available. Please check camera connection."
        )

    # 限制参数范围
    quality = max(1, min(100, quality))
    fps = max(1, min(Config.MAX_FPS, fps))

    logging.info(f"Starting MJPEG stream: quality={quality}, fps={fps}")

    return StreamingResponse(
        generate_mjpeg(quality, fps),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/snapshot")
async def get_snapshot(quality: int = 90):
    """获取单帧快照.

    Args:
        quality: JPEG 质量 (1-100)

    Returns:
        StreamingResponse with JPEG image

    Examples:
        curl http://10.42.0.75:8002/snapshot --output photo.jpg
    """
    if camera_manager._camera is None:
        raise HTTPException(
            status_code=503, detail="Camera not available. Please check camera connection."
        )

    frame = camera_manager.get_frame()
    if frame is None:
        raise HTTPException(status_code=500, detail="Failed to capture frame")

    # 编码为 JPEG
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), max(1, min(100, quality))]
    ret, encoded = cv2.imencode(".jpg", frame, encode_param)
    if not ret:
        raise HTTPException(status_code=500, detail="Failed to encode frame")

    jpeg_bytes = encoded.tobytes()

    return StreamingResponse(
        iter([jpeg_bytes]),
        media_type="image/jpeg",
        headers={
            "Content-Disposition": "attachment; filename=snapshot.jpg",
            "Content-Length": str(len(jpeg_bytes)),
        },
    )


@app.get("/status")
async def get_status():
    """获取摄像头状态.

    Returns:
        摄像头状态信息
    """
    if camera_manager._camera is None:
        return {
            "available": False,
            "message": "Camera not initialized",
            "backend": None,
        }

    width, height = camera_manager.get_resolution()
    fps = camera_manager.get_fps()

    return {
        "available": True,
        "backend": camera_manager._backend,
        "resolution": {"width": width, "height": height},
        "fps": fps,
        "specs": camera_manager._specs,
    }


@app.get("/info")
async def get_info():
    """获取摄像头详细信息.

    Returns:
        摄像头规格信息
    """
    if camera_manager._camera is None:
        raise HTTPException(status_code=503, detail="Camera not available")

    width, height = camera_manager.get_resolution()
    fps = camera_manager.get_fps()

    return {
        "backend": camera_manager._backend,
        "resolution": {"width": width, "height": height},
        "fps": fps,
        "specs": camera_manager._specs,
    }


@app.get("/health")
async def health_check():
    """健康检查."""
    return {"status": "healthy"}


# ===== 主函数 =====
def main():
    """主函数."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logging.info("Starting Camera Stream Service...")
    logging.info(f"API port: {Config.PORT}")
    logging.info(f"API host: {Config.HOST}")

    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
