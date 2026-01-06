#!/usr/bin/env python3
"""Reachy Mini 音频流服务 - REST API 服务端

这个服务可以在局域网内被其他设备调用，实现远程音频播放控制。

运行方式:
    python3 audio_stream_server.py

API 端点:
    POST /stream/start       - 启动 UDP 音频流接收 (OPUS 编码)
    POST /stream/start_pcm   - 启动 UDP 音频流接收 (原始 PCM)
    POST /stream/stop        - 停止音频流接收
    GET  /stream/status      - 获取当前状态
    POST /stream/play_url    - 从 URL 播放音频
    POST /stream/play_file   - 播放本地文件

端口: 8001
"""

import asyncio
import logging
import os
import tempfile
import threading
import time
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
import requests
import soundfile as sf
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    import gi
except ImportError as e:
    raise ImportError(
        "The 'gi' module is required. "
        "Please install GStreamer python bindings."
    ) from e

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")

from gi.repository import GLib, Gst  # noqa: E402


# ===== 配置 =====
class Config:
    """服务配置."""

    # API 服务配置
    HOST = "0.0.0.0"  # 监听所有网络接口，支持局域网访问
    PORT = 8001

    # 音频流接收配置
    UDP_PORT = 5001

    # 音频设备配置
    AUDIO_SINK_DEVICE = "reachymini_audio_sink"
    AUDIO_LATENCY = 200  # ms

    # 音频播放配置
    SAMPLE_RATE = 48000
    CHANNELS = 1


# ===== API 请求模型 =====
class StreamStartRequest(BaseModel):
    """启动流接收的请求."""

    port: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


class PlayUrlRequest(BaseModel):
    """播放 URL 的请求."""

    url: str
    sample_rate: Optional[int] = None


class PlayFileRequest(BaseModel):
    """播放文件的请求."""

    file_path: str
    sample_rate: Optional[int] = None


# ===== GStreamer OPUS 音频流接收器 =====
class UDPAudioStreamReceiver:
    """使用 GStreamer 接收 UDP OPUS 音频流并播放."""

    def __init__(
        self,
        port: int = Config.UDP_PORT,
        audio_device: str = Config.AUDIO_SINK_DEVICE,
        sample_rate: int = Config.SAMPLE_RATE,
        channels: int = Config.CHANNELS,
    ):
        """初始化音频流接收器.

        Args:
            port: UDP 接收端口
            audio_device: ALSA 音频输出设备
            sample_rate: 采样率
            channels: 通道数 (1=单声道, 2=立体声)
        """
        self._logger = logging.getLogger(__name__)
        self._port = port
        self._audio_device = audio_device
        self._sample_rate = sample_rate
        self._channels = channels

        self._pipeline: Optional[Gst.Pipeline] = None
        self._loop: Optional[GLib.MainLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False

        # 初始化 GStreamer
        Gst.init(None)

    def _create_pipeline(self) -> Gst.Pipeline:
        """创建 GStreamer 管道 (OPUS).

        管道结构:
            udpsrc ! capsfilter ! rtpjitterbuffer ! rtpopusdepay !
            opusdec ! audioconvert ! audioresample ! alsasink
        """
        self._logger.info(f"Creating OPUS audio pipeline for port {self._port}")

        pipeline = Gst.Pipeline.new(f"audio_stream_receiver_{self._port}")

        # 创建元素
        udpsrc = Gst.ElementFactory.make("udpsrc")
        udpsrc.set_property("port", self._port)

        # 设置 RTP OPUS caps
        caps_str = (
            f"application/x-rtp,media=audio,encoding-name=OPUS,"
            f"payload=96,clock-rate={self._sample_rate}"
        )
        if self._channels == 1:
            caps_str += ",encoding-params=(string)1"
        else:
            caps_str += ",encoding-params=(string)2"

        caps = Gst.Caps.from_string(caps_str)
        capsfilter = Gst.ElementFactory.make("capsfilter")
        capsfilter.set_property("caps", caps)

        # Jitter buffer 用于平滑网络抖动
        rtpjitterbuffer = Gst.ElementFactory.make("rtpjitterbuffer")
        rtpjitterbuffer.set_property("latency", Config.AUDIO_LATENCY)

        # RTP OPUS 解码
        rtpopusdepay = Gst.ElementFactory.make("rtpopusdepay")
        opusdec = Gst.ElementFactory.make("opusdec")

        # 音频处理
        queue = Gst.ElementFactory.make("queue")
        audioconvert = Gst.ElementFactory.make("audioconvert")
        audioresample = Gst.ElementFactory.make("audioresample")

        # 输出设备
        alsasink = Gst.ElementFactory.make("alsasink")
        alsasink.set_property("device", self._audio_device)
        # sync=False 减少延迟
        alsasink.set_property("sync", False)

        # 验证所有元素创建成功
        elements = [
            udpsrc,
            capsfilter,
            rtpjitterbuffer,
            rtpopusdepay,
            opusdec,
            queue,
            audioconvert,
            audioresample,
            alsasink,
        ]
        if not all(elements):
            missing = [e for e in elements if e is None]
            raise RuntimeError(f"Failed to create GStreamer elements: {missing}")

        # 添加到管道
        for elem in elements:
            pipeline.add(elem)

        # 连接元素
        udpsrc.link(capsfilter)
        capsfilter.link(rtpjitterbuffer)
        rtpjitterbuffer.link(rtpopusdepay)
        rtpopusdepay.link(opusdec)
        opusdec.link(queue)
        queue.link(audioconvert)
        audioconvert.link(audioresample)
        audioresample.link(alsasink)

        # 设置总线监控
        bus = pipeline.get_bus()
        bus.add_watch(GLib.PRIORITY_DEFAULT, self._on_bus_message, None)

        return pipeline

    def _on_bus_message(
        self, bus: Gst.Bus, msg: Gst.Message, user_data
    ) -> bool:
        """处理 GStreamer 总线消息."""
        t = msg.type
        if t == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            self._logger.error(f"GStreamer error: {err} - {debug}")
            self._is_running = False
            if self._loop:
                self._loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = msg.parse_warning()
            self._logger.warning(f"GStreamer warning: {err} - {debug}")
        elif t == Gst.MessageType.EOS:
            self._logger.info("End of stream")
            self._is_running = False
            if self._loop:
                self._loop.quit()
        elif t == Gst.MessageType.STATE_CHANGED:
            if msg.src == self._pipeline:
                old, new, pending = msg.parse_state_changed()
                self._logger.debug(f"Pipeline state: {old} -> {new}")
        elif t == Gst.MessageType.ELEMENT:
            msg.get_structure().print_to_log()

        return True

    def start(self) -> None:
        """启动音频流接收."""
        if self._is_running:
            self._logger.warning("Stream receiver already running")
            return

        self._logger.info(
            f"Starting OPUS audio stream receiver on port {self._port}, "
            f"device: {self._audio_device}, "
            f"sample_rate: {self._sample_rate}, "
            f"channels: {self._channels}"
        )

        try:
            # 创建管道
            self._pipeline = self._create_pipeline()

            # 创建 GLib 主循环
            self._loop = GLib.MainLoop()

            # 在独立线程中运行 GLib 循环
            self._thread = threading.Thread(
                target=self._loop.run, daemon=True
            )
            self._thread.start()

            # 启动管道
            ret = self._pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Failed to start pipeline")

            self._is_running = True
            self._logger.info("OPUS audio stream receiver started successfully")

        except Exception as e:
            self._logger.error(f"Failed to start stream receiver: {e}")
            self.stop()
            raise

    def stop(self) -> None:
        """停止音频流接收."""
        if not self._is_running:
            return

        self._logger.info("Stopping audio stream receiver")

        self._is_running = False

        if self._pipeline:
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None

        if self._loop:
            self._loop.quit()
            self._loop = None

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        self._logger.info("Audio stream receiver stopped")

    @property
    def is_running(self) -> bool:
        """检查接收器是否正在运行."""
        return self._is_running


# ===== GStreamer PCM 音频流接收器 =====
class PCMAudioStreamReceiver:
    """使用 GStreamer 接收 UDP 原始 PCM 音频流并播放."""

    def __init__(
        self,
        port: int = Config.UDP_PORT,
        audio_device: str = Config.AUDIO_SINK_DEVICE,
        sample_rate: int = Config.SAMPLE_RATE,
        channels: int = Config.CHANNELS,
    ):
        """初始化 PCM 音频流接收器.

        Args:
            port: UDP 接收端口
            audio_device: ALSA 音频输出设备
            sample_rate: 采样率
            channels: 通道数 (1=单声道, 2=立体声)
        """
        self._logger = logging.getLogger(__name__)
        self._port = port
        self._audio_device = audio_device
        self._sample_rate = sample_rate
        self._channels = channels

        self._pipeline: Optional[Gst.Pipeline] = None
        self._loop: Optional[GLib.MainLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False

        # 初始化 GStreamer
        Gst.init(None)

    def _create_pipeline(self) -> Gst.Pipeline:
        """创建 GStreamer 管道 (PCM).

        管道结构:
            udpsrc ! capsfilter ! queue ! audioconvert ! audioresample ! alsasink
        """
        self._logger.info(f"Creating PCM audio pipeline for port {self._port}")

        pipeline = Gst.Pipeline.new(f"pcm_stream_receiver_{self._port}")

        # 创建元素
        udpsrc = Gst.ElementFactory.make("udpsrc")
        udpsrc.set_property("port", self._port)

        # 设置 PCM caps (S16LE, mono, 48kHz)
        caps_str = (
            f"audio/x-raw,format=S16LE,rate={self._sample_rate},"
            f"channels={self._channels},layout=interleaved"
        )
        caps = Gst.Caps.from_string(caps_str)
        capsfilter = Gst.ElementFactory.make("capsfilter")
        capsfilter.set_property("caps", caps)

        # 音频处理
        queue = Gst.ElementFactory.make("queue")
        queue.set_property("max-size-buffers", 10)  # 限制缓冲区大小减少延迟

        audioconvert = Gst.ElementFactory.make("audioconvert")
        audioresample = Gst.ElementFactory.make("audioresample")

        # 输出设备
        alsasink = Gst.ElementFactory.make("alsasink")
        alsasink.set_property("device", self._audio_device)
        # sync=False 减少延迟
        alsasink.set_property("sync", False)

        # 验证所有元素创建成功
        elements = [udpsrc, capsfilter, queue, audioconvert, audioresample, alsasink]
        if not all(elements):
            missing = [e for e in elements if e is None]
            raise RuntimeError(f"Failed to create GStreamer elements: {missing}")

        # 添加到管道
        for elem in elements:
            pipeline.add(elem)

        # 连接元素
        udpsrc.link(capsfilter)
        capsfilter.link(queue)
        queue.link(audioconvert)
        audioconvert.link(audioresample)
        audioresample.link(alsasink)

        # 设置总线监控
        bus = pipeline.get_bus()
        bus.add_watch(GLib.PRIORITY_DEFAULT, self._on_bus_message, None)

        return pipeline

    def _on_bus_message(
        self, bus: Gst.Bus, msg: Gst.Message, user_data
    ) -> bool:
        """处理 GStreamer 总线消息."""
        t = msg.type
        if t == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            self._logger.error(f"GStreamer error: {err} - {debug}")
            self._is_running = False
            if self._loop:
                self._loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = msg.parse_warning()
            self._logger.warning(f"GStreamer warning: {err} - {debug}")
        elif t == Gst.MessageType.EOS:
            self._logger.info("End of stream")
            self._is_running = False
            if self._loop:
                self._loop.quit()
        elif t == Gst.MessageType.STATE_CHANGED:
            if msg.src == self._pipeline:
                old, new, pending = msg.parse_state_changed()
                self._logger.debug(f"Pipeline state: {old} -> {new}")

        return True

    def start(self) -> None:
        """启动 PCM 音频流接收."""
        if self._is_running:
            self._logger.warning("PCM stream receiver already running")
            return

        self._logger.info(
            f"Starting PCM audio stream receiver on port {self._port}, "
            f"device: {self._audio_device}, "
            f"sample_rate: {self._sample_rate}, "
            f"channels: {self._channels}"
        )

        try:
            # 创建管道
            self._pipeline = self._create_pipeline()

            # 创建 GLib 主循环
            self._loop = GLib.MainLoop()

            # 在独立线程中运行 GLib 循环
            self._thread = threading.Thread(
                target=self._loop.run, daemon=True
            )
            self._thread.start()

            # 启动管道
            ret = self._pipeline.set_state(Gst.State.PLAYING)
            if ret == Gst.StateChangeReturn.FAILURE:
                raise RuntimeError("Failed to start pipeline")

            self._is_running = True
            self._logger.info("PCM audio stream receiver started successfully")

        except Exception as e:
            self._logger.error(f"Failed to start PCM stream receiver: {e}")
            self.stop()
            raise

    def stop(self) -> None:
        """停止音频流接收."""
        if not self._is_running:
            return

        self._logger.info("Stopping PCM audio stream receiver")

        self._is_running = False

        if self._pipeline:
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None

        if self._loop:
            self._loop.quit()
            self._loop = None

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        self._logger.info("PCM audio stream receiver stopped")

    @property
    def is_running(self) -> bool:
        """检查接收器是否正在运行."""
        return self._is_running


# ===== 音频文件播放器 =====
class AudioFilePlayer:
    """播放音频文件或 URL."""

    def __init__(self, audio_device: str = Config.AUDIO_SINK_DEVICE):
        """初始化播放器.

        Args:
            audio_device: ALSA 音频输出设备
        """
        self._logger = logging.getLogger(__name__)
        self._audio_device = audio_device
        Gst.init(None)

    def play_file(
        self,
        file_path: str,
        target_sample_rate: int = 16000,
        blocking: bool = False,
    ) -> float:
        """播放音频文件.

        Args:
            file_path: 文件路径
            target_sample_rate: 目标采样率
            blocking: 是否阻塞等待播放完成

        Returns:
            音频时长（秒）
        """
        self._logger.info(f"Playing file: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 读取音频文件
        data, samplerate = sf.read(file_path, dtype="float32")

        self._logger.info(
            f"Audio info - Sample rate: {samplerate} Hz, "
            f"Channels: {data.shape[1] if len(data.shape) > 1 else 1}"
        )

        # 转换为单声道
        if data.ndim > 1:
            data = np.mean(data, axis=1)

        # 重采样
        if samplerate != target_sample_rate:
            from scipy import signal

            num_samples = int(len(data) * (target_sample_rate / samplerate))
            data = signal.resample(data, num_samples)

        # 计算时长
        duration = len(data) / target_sample_rate

        # 使用 GStreamer playbin 播放
        playbin = Gst.ElementFactory.make("playbin", "player")
        if not playbin:
            raise RuntimeError("Failed to create playbin element")

        playbin.set_property("uri", f"file://{file_path}")

        # 设置输出设备
        alsasink = Gst.ElementFactory.make("alsasink")
        alsasink.set_property("device", self._audio_device)
        playbin.set_property("audio-sink", alsasink)

        # 创建总线监听
        loop = GLib.MainLoop()
        bus = playbin.get_bus()

        def on_bus_message(bus, msg, loop):
            if msg.type == Gst.MessageType.EOS:
                loop.quit()
            elif msg.type == Gst.MessageType.ERROR:
                err, debug = msg.parse_error()
                self._logger.error(f"Playback error: {err} - {debug}")
                loop.quit()
            return True

        bus.add_watch(GLib.PRIORITY_DEFAULT, on_bus_message, loop)

        # 启动播放
        playbin.set_state(Gst.State.PLAYING)

        if blocking:
            # 在当前线程运行
            try:
                loop.run()
            except KeyboardInterrupt:
                pass
            finally:
                playbin.set_state(Gst.State.NULL)

        return duration

    def play_url(
        self,
        url: str,
        target_sample_rate: int = 16000,
    ) -> float:
        """从 URL 播放音频.

        Args:
            url: 音频 URL
            target_sample_rate: 目标采样率

        Returns:
            音频时长（秒）
        """
        self._logger.info(f"Playing from URL: {url}")

        # 下载音频
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # 确定文件扩展名
        if url.endswith(".mp3"):
            suffix = ".mp3"
        elif url.endswith(".flac"):
            suffix = ".flac"
        elif url.endswith(".ogg"):
            suffix = ".ogg"
        elif url.endswith(".wav"):
            suffix = ".wav"
        else:
            # 根据内容类型判断
            content_type = response.headers.get("content-type", "")
            if "mpeg" in content_type or "mp3" in content_type:
                suffix = ".mp3"
            elif "flac" in content_type:
                suffix = ".flac"
            elif "ogg" in content_type:
                suffix = ".ogg"
            else:
                suffix = ".wav"

        # 写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name

        try:
            duration = self.play_file(temp_path, target_sample_rate)
            return duration
        finally:
            # 清理临时文件
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ===== FastAPI 应用 =====
# 全局接收器实例
stream_receiver: Optional[UDPAudioStreamReceiver] = None
pcm_stream_receiver: Optional[PCMAudioStreamReceiver] = None
file_player = AudioFilePlayer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    # 启动时
    logging.info("Audio Stream Service starting...")
    yield
    # 关闭时
    logging.info("Audio Stream Service shutting down...")
    if stream_receiver:
        stream_receiver.stop()
    if pcm_stream_receiver:
        pcm_stream_receiver.stop()


app = FastAPI(
    title="Reachy Mini Audio Stream Service",
    description="局域网音频流播放服务",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """根路径."""
    return {
        "service": "Reachy Mini Audio Stream Service",
        "version": "1.0.0",
        "status": "running",
    }


@app.post("/stream/start")
async def start_stream(request: StreamStartRequest):
    """启动 OPUS 音频流接收.

    Args:
        request: 启动参数

    Returns:
        启动状态
    """
    global stream_receiver

    if stream_receiver and stream_receiver.is_running:
        raise HTTPException(
            status_code=409, detail="Stream receiver already running"
        )

    # 使用请求参数或默认值
    port = request.port or Config.UDP_PORT
    sample_rate = request.sample_rate or Config.SAMPLE_RATE
    channels = request.channels or Config.CHANNELS

    try:
        stream_receiver = UDPAudioStreamReceiver(
            port=port,
            audio_device=Config.AUDIO_SINK_DEVICE,
            sample_rate=sample_rate,
            channels=channels,
        )
        stream_receiver.start()

        return {
            "status": "started",
            "format": "OPUS",
            "port": port,
            "sample_rate": sample_rate,
            "channels": channels,
            "audio_device": Config.AUDIO_SINK_DEVICE,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stream/start_pcm")
async def start_pcm_stream(request: StreamStartRequest):
    """启动 PCM 音频流接收 (用于原始音频推流).

    Args:
        request: 启动参数

    Returns:
        启动状态
    """
    global pcm_stream_receiver

    if pcm_stream_receiver and pcm_stream_receiver.is_running:
        raise HTTPException(
            status_code=409, detail="PCM stream receiver already running"
        )

    # 使用请求参数或默认值
    port = request.port or Config.UDP_PORT
    sample_rate = request.sample_rate or Config.SAMPLE_RATE
    channels = request.channels or Config.CHANNELS

    try:
        pcm_stream_receiver = PCMAudioStreamReceiver(
            port=port,
            audio_device=Config.AUDIO_SINK_DEVICE,
            sample_rate=sample_rate,
            channels=channels,
        )
        pcm_stream_receiver.start()

        return {
            "status": "started",
            "format": "PCM S16LE",
            "port": port,
            "sample_rate": sample_rate,
            "channels": channels,
            "audio_device": Config.AUDIO_SINK_DEVICE,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stream/stop")
async def stop_stream():
    """停止音频流接收."""
    global stream_receiver, pcm_stream_receiver

    stopped = []

    if stream_receiver and stream_receiver.is_running:
        stream_receiver.stop()
        stopped.append("OPUS")

    if pcm_stream_receiver and pcm_stream_receiver.is_running:
        pcm_stream_receiver.stop()
        stopped.append("PCM")

    if not stopped:
        raise HTTPException(status_code=404, detail="Stream receiver not running")

    return {"status": "stopped", "formats": stopped}


@app.get("/stream/status")
async def get_stream_status():
    """获取流接收状态."""
    status = {
        "opus_running": stream_receiver is not None and stream_receiver.is_running,
        "pcm_running": pcm_stream_receiver is not None and pcm_stream_receiver.is_running,
    }

    if stream_receiver:
        status["opus_port"] = stream_receiver._port

    if pcm_stream_receiver:
        status["pcm_port"] = pcm_stream_receiver._port

    return status


@app.post("/stream/play_url")
async def play_url(request: PlayUrlRequest, background_tasks: BackgroundTasks):
    """从 URL 播放音频.

    Args:
        request: 播放请求
        background_tasks: FastAPI 后台任务

    Returns:
        播放状态
    """
    target_sr = request.sample_rate or 16000

    async def play_task():
        try:
            file_player.play_url(request.url, target_sr)
        except Exception as e:
            logging.error(f"Failed to play URL: {e}")

    background_tasks.add_task(play_task)

    return {
        "status": "playing",
        "url": request.url,
        "target_sample_rate": target_sr,
    }


@app.post("/stream/play_file")
async def play_file(request: PlayFileRequest, background_tasks: BackgroundTasks):
    """播放本地音频文件.

    Args:
        request: 播放请求
        background_tasks: FastAPI 后台任务

    Returns:
        播放状态
    """
    target_sr = request.sample_rate or 16000

    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

    async def play_task():
        try:
            file_player.play_file(request.file_path, target_sr)
        except Exception as e:
            logging.error(f"Failed to play file: {e}")

    background_tasks.add_task(play_task)

    return {
        "status": "playing",
        "file_path": request.file_path,
        "target_sample_rate": target_sr,
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

    logging.info("Starting Audio Stream Service...")
    logging.info(f"UDP port: {Config.UDP_PORT}")
    logging.info(f"Audio device: {Config.AUDIO_SINK_DEVICE}")
    logging.info(f"API port: {Config.PORT}")
    logging.info(f"Listen on: {Config.HOST}:{Config.PORT}")
    logging.info("")
    logging.info("API 端点:")
    logging.info("  POST /stream/start      - 启动 OPUS UDP 音频流接收")
    logging.info("  POST /stream/start_pcm  - 启动 PCM UDP 音频流接收")
    logging.info("  POST /stream/stop       - 停止音频流接收")
    logging.info("  GET  /stream/status     - 获取当前状态")
    logging.info("  POST /stream/play_url   - 从 URL 播放音频")
    logging.info("  POST /stream/play_file  - 播放本地文件")
    logging.info("")
    logging.info("局域网访问示例:")
    logging.info(f"  curl http://<ROBOT_IP>:8001/stream/status")
    logging.info("")

    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
