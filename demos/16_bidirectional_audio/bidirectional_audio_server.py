#!/usr/bin/env python3
import asyncio
import logging
import os
import tempfile
import threading
from contextlib import asynccontextmanager
from typing import Optional, List

import numpy as np
import requests
import soundfile as sf
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# 必须先导入 gi 并声明版本
import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
from gi.repository import GLib, Gst, GstApp

# 初始化 GStreamer
Gst.init(None)

# ===== 配置 =====
class Config:
    HOST = "0.0.0.0"
    PORT = 8002
    AUDIO_SINK_DEVICE = "reachymini_audio_sink"
    AUDIO_SRC_DEVICE = "reachymini_audio_src" # 麦克风设备
    SAMPLE_RATE_PUSH = 48000
    SAMPLE_RATE_PULL = 16000 # 录音采样率

# ===== 模型 =====
class PlayFileRequest(BaseModel):
    file_path: str
    sample_rate: Optional[int] = None

# ===== 麦克风转发器 (上行链路) =====
class AudioMicForwarder:
    def __init__(self):
        self._logger = logging.getLogger("MicForwarder")
        self.active_connections: List[WebSocket] = []
        self._pipeline: Optional[Gst.Pipeline] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        if not sample:
            return Gst.FlowReturn.OK

        buffer = sample.get_buffer()
        success, info = buffer.map(Gst.MapFlags.READ)
        if success:
            data = info.data
            # 广播给所有连上的 WS 客户端
            if self._loop:
                for ws in list(self.active_connections):  # 使用 list() 避免迭代时修改
                    try:
                        asyncio.run_coroutine_threadsafe(ws.send_bytes(data), self._loop)
                    except Exception as e:
                        self._logger.warning(f"发送失败: {e}")
            buffer.unmap(info)
        return Gst.FlowReturn.OK

    def start(self, loop: asyncio.AbstractEventLoop):
        if self._pipeline: return
        self._loop = loop
        # 管道：采集 -> 转换 -> 编码(Opus) -> 这里的 appsink 抓取字节流
        pipeline_str = (
            f"alsasrc device={Config.AUDIO_SRC_DEVICE} ! "
            f"audioconvert ! audioresample ! "
            f"opusenc bitrate=32000 ! "
            f"appsink name=sink emit-signals=True max-buffers=10 drop=True"
        )
        self._pipeline = Gst.parse_launch(pipeline_str)
        sink = self._pipeline.get_by_name("sink")
        sink.connect("new-sample", self._on_new_sample)
        self._pipeline.set_state(Gst.State.PLAYING)
        self._logger.info("🎙️ 麦克风采集已启动")

    def stop(self):
        if self._pipeline:
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
            self._logger.info("🎙️ 麦克风采集已停止")

# ===== 文件播放器 (下行链路) =====
class AudioFilePlayer:
    def __init__(self):
        self._logger = logging.getLogger("FilePlayer")

    def play_file(self, file_path: str):
        playbin = Gst.ElementFactory.make("playbin", "player")
        playbin.set_property("uri", f"file://{os.path.abspath(file_path)}")
        sink = Gst.ElementFactory.make("alsasink")
        sink.set_property("device", Config.AUDIO_SINK_DEVICE)
        playbin.set_property("audio-sink", sink)
        
        bus = playbin.get_bus()
        playbin.set_state(Gst.State.PLAYING)
        msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR)
        playbin.set_state(Gst.State.NULL)

# ===== FastAPI 实例 =====
mic_forwarder = AudioMicForwarder()
file_player = AudioFilePlayer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("🚀 双向音频服务已就绪")
    yield
    mic_forwarder.stop()

app = FastAPI(lifespan=lifespan)

# 1. 麦克风 WebSocket 接口
@app.websocket("/audio/mic")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    mic_forwarder.active_connections.append(websocket)
    if len(mic_forwarder.active_connections) == 1:
        mic_forwarder.start(asyncio.get_event_loop())
    try:
        while True:
            await websocket.receive_text() # 保持连接
    except WebSocketDisconnect:
        mic_forwarder.active_connections.remove(websocket)
        if not mic_forwarder.active_connections:
            mic_forwarder.stop()

# 2. 文件播放接口
@app.post("/stream/play_file")
async def play_file(request: PlayFileRequest, background_tasks: BackgroundTasks):
    if not os.path.exists(request.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    background_tasks.add_task(file_player.play_file, request.file_path)
    return {"status": "playing", "file": request.file_path}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)