#!/usr/bin/env python3
"""Demo 18: WebRTC 视频流转 HTTP 流

这个 Demo 将 WebRTC 视频流转换为普通的 HTTP MJPEG 流，
使其可以在浏览器中直接播放，无需 WebRTC 客户端。

功能特点:
- 使用 GStreamer 接收 WebRTC 流（参考 Demo 11 的实现方式）
- 将视频帧转换为 MJPEG 格式
- 通过 Flask 提供 HTTP 视频流服务
- 简单的网页前端在浏览器中播放

架构:
机器人 --[WebRTC]--> 本服务 --[MJPEG]--> 浏览器

依赖:
    pip install flask opencv-python numpy

GStreamer 依赖:
    需要安装 GStreamer 和 WebRTC 插件

运行:
    python3 18.py --signaling-host <机器人IP>

然后在浏览器访问:
    http://localhost:5000
"""

import argparse
import sys
import time
import threading
import io
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
    from flask import Flask, Response, render_template
except ImportError:
    print("错误: 请安装 flask")
    print("pip install flask")
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


class WebRTCVideoStreamer:
    """WebRTC 视频流接收器，转换为 MJPEG"""

    def __init__(self, signalling_host: str, signalling_port: int = 8443, peer_name: str = "reachymini"):
        """初始化 WebRTC 视频流接收器

        Args:
            signalling_host: 信令服务器地址（机器人 IP）
            signalling_port: 信令服务器端口，默认 8443
            peer_name: 对等端名称，默认 "reachymini"
        """
        self.signalling_host = signalling_host
        self.signalling_port = signalling_port
        self.peer_name = peer_name

        # 视频帧缓冲区
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.frame_count = 0

        # 初始化 GStreamer
        Gst.init(None)

        print(f"[视频] 初始化 WebRTC 连接...")
        print(f"[视频] 信令服务器: ws://{signalling_host}:{signalling_port}")
        print(f"[视频] 对等端名称: {peer_name}")

        # 创建 GStreamer 管道
        self.pipeline = Gst.Pipeline.new("webrtc-consumer")
        self.source = Gst.ElementFactory.make("webrtcsrc")
        self.appsink = None

        if not self.pipeline or not self.source:
            print("[错误] 无法创建 GStreamer 管道")
            sys.exit(1)

        self.pipeline.add(self.source)

        # 连接到信令服务器并查找对等端
        try:
            peer_id = find_producer_peer_id_by_name(
                signalling_host, signalling_port, peer_name
            )
            print(f"[视频] 找到对等端 ID: {peer_id}")
        except Exception as e:
            print(f"[错误] 无法连接信令服务器: {e}")
            print(f"[提示] 请检查机器人 IP 是否正确: {signalling_host}")
            sys.exit(1)

        # 连接信号
        self.source.connect("pad-added", self._on_pad_added)

        # 配置信令
        signaller = self.source.get_property("signaller")
        signaller.set_property("producer-peer-id", peer_id)
        signaller.set_property("uri", f"ws://{signalling_host}:{signalling_port}")

        print("[视频] WebRTC 管道设置完成")

    def _on_pad_added(self, webrtcsrc, pad):
        """当新的 pad 添加时调用"""
        pad_name = pad.get_name()

        if pad_name.startswith("video"):
            print("[视频] 视频流已连接!")
            # 创建视频转换元素
            convert = Gst.ElementFactory.make("videoconvert")
            capsfilter = Gst.ElementFactory.make("capsfilter")
            self.appsink = Gst.ElementFactory.make("appsink")

            # 设置输出格式为 BGR (OpenCV 格式)
            caps = Gst.Caps.from_string("video/x-raw, format=BGR")
            capsfilter.set_property("caps", caps)

            # 配置 appsink
            self.appsink.set_property("emit-signals", True)
            self.appsink.set_property("sync", False)  # 不同步，降低延迟
            self.appsink.set_property("max-buffers", 1)  # 只保留最新帧
            self.appsink.set_property("drop", True)  # 丢弃旧帧

            # 添加到管道
            self.pipeline.add(convert)
            self.pipeline.add(capsfilter)
            self.pipeline.add(self.appsink)

            # 连接元素
            pad.link(convert.get_static_pad("sink"))
            convert.link(capsfilter)
            capsfilter.link(self.appsink)

            # 同步状态
            convert.sync_state_with_parent()
            capsfilter.sync_state_with_parent()
            self.appsink.sync_state_with_parent()

            # 设置低延迟
            if isinstance(webrtcsrc, Gst.Bin):
                webrtc = webrtcsrc.get_by_name("webrtcbin0")
                if webrtc:
                    webrtc.set_property("latency", 0)

            print("[视频] 视频管道已建立")

        elif pad_name.startswith("audio"):
            # 音频流不处理
            pass

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

            # 获取视频尺寸
            structure = caps.get_structure(0)
            height = structure.get_value("height")
            width = structure.get_value("width")

            # 提取数据到 numpy 数组
            arr = np.ndarray(
                (height, width, 3),
                buffer=buf.extract_dup(0, buf.get_size()),
                dtype=np.uint8
            )

            return arr

        except Exception as e:
            return None

    def start(self):
        """启动视频流"""
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("[错误] 无法启动视频管道")
            return False
        print("[视频] 视频流已启动")
        return True

    def stop(self):
        """停止视频流"""
        self.pipeline.set_state(Gst.State.NULL)
        print("[视频] 视频流已停止")


class MJPEGServer:
    """MJPEG HTTP 服务器"""

    def __init__(self, streamer: WebRTCVideoStreamer, host: str = "0.0.0.0", port: int = 5000):
        """初始化 MJPEG 服务器

        Args:
            streamer: WebRTC 视频流接收器
            host: 监听地址
            port: 监听端口
        """
        self.streamer = streamer
        self.host = host
        self.port = port

        # 创建 Flask 应用
        self.app = Flask(__name__)
        self.app.template_folder = str(Path(__file__).parent / "templates")

        # 设置路由
        self._setup_routes()

    def _setup_routes(self):
        """设置路由"""

        @self.app.route('/')
        def index():
            """主页面"""
            return render_template('index.html',
                                   signalling_host=self.streamer.signalling_host)

        @self.app.route('/video_feed')
        def video_feed():
            """视频流路由

            返回 MJPEG 流，浏览器可以通过 <img> 标签直接显示
            """
            def generate():
                """生成 MJPEG 流"""
                while True:
                    frame = self.streamer.get_frame()

                    if frame is not None:
                        # 编码为 JPEG
                        ret, jpeg = cv2.imencode('.jpg', frame,
                                                 [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                        if ret:
                            # 生成 multipart 响应
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                    else:
                        # 如果没有帧，发送一个等待帧
                        time.sleep(0.1)

            return Response(generate(),
                           mimetype='multipart/x-mixed-replace; boundary=frame')

        @self.app.route('/status')
        def status():
            """状态检查"""
            return {
                'status': 'running',
                'signalling_host': self.streamer.signalling_host,
                'signalling_port': self.streamer.signalling_port
            }

    def run(self):
        """启动服务器"""
        import socket

        # 获取本机 IP
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "127.0.0.1"

        print("=" * 60)
        print("Demo 18: WebRTC to MJPEG Stream")
        print("=" * 60)
        print(f"视频源: {self.streamer.signalling_host}")
        print()
        print("服务器已启动!")
        print("=" * 60)
        print(f"本地访问: http://localhost:{self.port}")
        print(f"局域网访问: http://{local_ip}:{self.port}")
        print()
        print("在浏览器中打开上述地址即可观看视频流")
        print("按 Ctrl+C 停止服务器")
        print("=" * 60)
        print()

        # 启动服务器
        self.app.run(host=self.host, port=self.port, debug=False, threaded=True)


def main():
    parser = argparse.ArgumentParser(
        description="Demo 18: WebRTC 视频流转 HTTP MJPEG 流"
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

    # 创建视频流接收器
    streamer = WebRTCVideoStreamer(
        args.signaling_host,
        args.signaling_port,
        args.peer_name
    )

    # 启动视频流
    if not streamer.start():
        print("[错误] 无法启动视频流")
        sys.exit(1)

    # 等待一下让视频流稳定
    print("[启动] 等待视频流稳定...")
    time.sleep(2)

    # 创建并启动 HTTP 服务器
    server = MJPEGServer(streamer, port=args.port)

    try:
        server.run()
    except KeyboardInterrupt:
        print("\n正在停止...")
    finally:
        streamer.stop()


if __name__ == "__main__":
    main()
