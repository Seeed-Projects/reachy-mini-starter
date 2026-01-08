#!/usr/bin/env python3
"""
Demo 17: Reachy Mini 网页控制与视频流 - 整合版

功能特点:
- 基于 Demo 15 的 WebSocket 低延迟控制
- 基于 Demo 18 的 WebRTC 视频流转换为 MJPEG
- 统一的 Flask 服务器同时提供控制和视频服务
- 模块化前端设计，便于维护和扩展

架构:
浏览器 <--[WebSocket]--> Flask 服务器 <--[HTTP POST]--> 机器人 API
     <--[MJPEG]-->      |
                      +--[WebRTC]--> 机器人视频流

控制链路参考: Demo 15 (15_web_realtime_control)
视频链路参考: Demo 18 (18_webrtc_to_http_stream)

依赖:
    pip install flask flask-socketio eventlet requests opencv-python numpy

GStreamer 依赖:
    需要安装 GStreamer 和 WebRTC 插件

运行:
    python server.py --signaling-host <机器人IP>

然后在浏览器访问:
    http://localhost:5000
"""

import argparse
import sys
import time
import threading
import math
import requests
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------- 依赖检查 ----------------------
try:
    import cv2
    import numpy as np
except ImportError:
    print("错误: 请安装 opencv-python 和 numpy")
    print("pip install opencv-python numpy")
    sys.exit(1)

try:
    from flask import Flask, render_template, Response
    from flask_socketio import SocketIO, emit
except ImportError:
    print("错误: 请安装 flask 和 flask-socketio")
    print("pip install flask flask-socketio eventlet")
    sys.exit(1)

try:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import GLib, Gst
    from gst_signalling.utils import find_producer_peer_id_by_name
except ImportError:
    print("错误: 未找到 GStreamer 或 reachy-mini 相关库")
    print("请确保已安装 GStreamer 和 reachy-mini SDK")
    sys.exit(1)

from config_loader import get_config

# 加载配置
robot_config = get_config()
ROBOT_API = robot_config.base_url


# =============================================================================
# WebRTC 视频流接收器 (来自 Demo 18)
# =============================================================================
class WebRTCVideoStreamer:
    """WebRTC 视频流接收器，转换为 MJPEG"""

    def __init__(self, signalling_host: str, signalling_port: int = 8443, peer_name: str = "reachymini"):
        self.signalling_host = signalling_host
        self.signalling_port = signalling_port
        self.peer_name = peer_name
        self.appsink = None

        # 初始化 GStreamer
        Gst.init(None)

        print(f"[视频] 初始化 WebRTC 连接...")
        print(f"[视频] 信令服务器: ws://{signalling_host}:{signalling_port}")

        # 创建 GStreamer 管道
        self.pipeline = Gst.Pipeline.new("webrtc-consumer")
        self.source = Gst.ElementFactory.make("webrtcsrc")

        if not self.pipeline or not self.source:
            print("[错误] 无法创建 GStreamer 管道")
            sys.exit(1)

        self.pipeline.add(self.source)

        # 查找对等端
        try:
            peer_id = find_producer_peer_id_by_name(
                signalling_host, signalling_port, peer_name
            )
            print(f"[视频] 找到对等端 ID: {peer_id}")
        except Exception as e:
            print(f"[错误] 无法连接信令服务器: {e}")
            sys.exit(1)

        # 连接信号
        self.source.connect("pad-added", self._on_pad_added)

        # 配置信令
        signaller = self.source.get_property("signaller")
        signaller.set_property("producer-peer-id", peer_id)
        signaller.set_property("uri", f"ws://{signalling_host}:{signalling_port}")

        print("[视频] WebRTC 管道设置完成")

    def _on_pad_added(self, webrtcsrc, pad):
        pad_name = pad.get_name()

        if pad_name.startswith("video"):
            print("[视频] 视频流已连接!")
            convert = Gst.ElementFactory.make("videoconvert")
            capsfilter = Gst.ElementFactory.make("capsfilter")
            self.appsink = Gst.ElementFactory.make("appsink")

            caps = Gst.Caps.from_string("video/x-raw, format=BGR")
            capsfilter.set_property("caps", caps)

            self.appsink.set_property("emit-signals", True)
            self.appsink.set_property("sync", False)
            self.appsink.set_property("max-buffers", 1)
            self.appsink.set_property("drop", True)

            self.pipeline.add(convert)
            self.pipeline.add(capsfilter)
            self.pipeline.add(self.appsink)

            pad.link(convert.get_static_pad("sink"))
            convert.link(capsfilter)
            capsfilter.link(self.appsink)

            convert.sync_state_with_parent()
            capsfilter.sync_state_with_parent()
            self.appsink.sync_state_with_parent()

            print("[视频] 视频管道已建立")

    def get_frame(self):
        """获取最新视频帧"""
        if self.appsink is None:
            return None

        try:
            sample = self.appsink.emit("try-pull-sample", 5 * Gst.MSECOND)
            if sample is None:
                return None

            buf = sample.get_buffer()
            caps = sample.get_caps()

            structure = caps.get_structure(0)
            height = structure.get_value("height")
            width = structure.get_value("width")

            arr = np.ndarray(
                (height, width, 3),
                buffer=buf.extract_dup(0, buf.get_size()),
                dtype=np.uint8
            )
            return arr
        except Exception:
            return None

    def start(self):
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("[错误] 无法启动视频管道")
            return False
        print("[视频] 视频流已启动")
        return True

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)
        print("[视频] 视频流已停止")


# =============================================================================
# Flask 应用 + WebSocket (来自 Demo 15)
# =============================================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'reachy-mini-webcam-control-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 视频流接收器 (全局变量)
video_streamer = None


@app.route('/')
def index():
    """主页面"""
    signalling_host = video_streamer.signalling_host if video_streamer else "127.0.0.1"
    return render_template('index.html', signalling_host=signalling_host)


@app.route('/video_feed')
def video_feed():
    """MJPEG 视频流"""
    def generate():
        while True:
            if video_streamer:
                frame = video_streamer.get_frame()
                if frame is not None:
                    ret, jpeg = cv2.imencode('.jpg', frame,
                                            [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.033)  # ~30 FPS

    return Response(generate(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/status')
def status():
    """状态检查"""
    return {
        'status': 'running',
        'robot_api': ROBOT_API,
        'video_connected': video_streamer is not None
    }


# =============================================================================
# WebSocket 事件处理 (来自 Demo 15)
# =============================================================================
@socketio.on('connect')
def handle_connect(data=None):
    print(f'客户端连接: {request.sid}')
    emit('connected', {'status': 'ok', 'robot_api': ROBOT_API})


@socketio.on('disconnect')
def handle_disconnect():
    print(f'客户端断开: {request.sid}')


@socketio.on('move_command')
def handle_move_command(data):
    """处理运动命令 - 度数转弧度"""
    try:
        # 头部姿态（度转弧度）
        roll_radians = math.radians(data.get('roll', 0.0))
        pitch_radians = math.radians(data.get('pitch', 0.0))
        yaw_radians = math.radians(data.get('yaw', 0.0))

        # 身体偏航（度转弧度）
        body_yaw_radians = math.radians(data.get('body_yaw', 0.0))

        # 天线角度（度转弧度）
        antennas_radians = [math.radians(a) for a in data.get('antennas', [0, 0])]

        payload = {
            'head_pose': {
                'x': data.get('position', {}).get('x', 0.0),
                'y': data.get('position', {}).get('y', 0.0),
                'z': data.get('position', {}).get('z', 0.0),
                'roll': roll_radians,
                'pitch': pitch_radians,
                'yaw': yaw_radians
            },
            'antennas': antennas_radians,
            'body_yaw': body_yaw_radians,
            'duration': 0.3,
            'interpolation': 'minjerk'
        }

        response = requests.post(
            f"{ROBOT_API}/move/goto",
            json=payload,
            timeout=5
        )

        if response.status_code == 200:
            emit('move_result', {'success': True})
        else:
            emit('move_result', {'success': False,
                               'error': f'API 错误: {response.status_code}'})

    except Exception as e:
        emit('move_result', {'success': False, 'error': str(e)})


@socketio.on('enable_motors')
def handle_enable_motors():
    try:
        response = requests.post(
            f"{ROBOT_API}/motors/set_mode/enabled",
            timeout=5
        )
        emit('motors_result', {
            'action': 'enable',
            'success': response.status_code == 200
        })
    except Exception as e:
        emit('motors_result', {
            'action': 'enable',
            'success': False,
            'error': str(e)
        })


@socketio.on('disable_motors')
def handle_disable_motors():
    try:
        response = requests.post(
            f"{ROBOT_API}/motors/set_mode/disabled",
            timeout=5
        )
        emit('motors_result', {
            'action': 'disable',
            'success': response.status_code == 200
        })
    except Exception as e:
        emit('motors_result', {
            'action': 'disable',
            'success': False,
            'error': str(e)
        })


# =============================================================================
# 主程序
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Demo 17: Reachy Mini 网页控制与视频流"
    )
    parser.add_argument(
        "-s", "--signaling-host",
        default="127.0.0.1",
        help="信令服务器地址（机器人 IP）"
    )
    parser.add_argument(
        "-p", "--signaling-port",
        type=int,
        default=8443,
        help="信令服务器端口"
    )
    parser.add_argument(
        "-n", "--peer-name",
        default="reachymini",
        help="对等端名称"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="HTTP 服务器端口"
    )
    args = parser.parse_args()

    global video_streamer

    print("=" * 60)
    print("Demo 17: Reachy Mini 网页控制与视频流")
    print("=" * 60)
    print()
    print(f"机器人配置: {robot_config}")
    print(f"机器人 API: {ROBOT_API}")
    print()

    # 创建并启动视频流
    video_streamer = WebRTCVideoStreamer(
        args.signaling_host,
        args.signaling_port,
        args.peer_name
    )

    if not video_streamer.start():
        print("[错误] 无法启动视频流")
        sys.exit(1)

    print("[启动] 等待视频流稳定...")
    time.sleep(2)

    # 获取本机 IP
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"

    print("=" * 60)
    print("服务器已启动!")
    print("=" * 60)
    print(f"本地访问: http://localhost:{args.port}")
    print(f"局域网访问: http://{local_ip}:{args.port}")
    print()
    print("功能:")
    print("  - WebSocket 低延迟控制")
    print("  - MJPEG 视频流显示")
    print()
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()

    try:
        socketio.run(app, host='0.0.0.0', port=args.port,
                    debug=False, allow_unsafe_werkzeug=True, threaded=True)
    except KeyboardInterrupt:
        print("\n正在停止...")
    finally:
        if video_streamer:
            video_streamer.stop()


if __name__ == '__main__':
    main()
