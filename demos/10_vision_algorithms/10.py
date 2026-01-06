#!/usr/bin/env python3
"""Reachy Mini WebRTC 视频流接收演示 + YOLO 检测

使用 GStreamer WebRTC 接收视频，转换为 OpenCV 格式并运行 YOLOv8 检测。
"""

import argparse
import sys
import time
from pathlib import Path

# ---------------------- 依赖检查 ----------------------
try:
    import cv2
    import numpy as np
    from ultralytics import YOLO
except ImportError as e:
    print("=" * 60)
    print(f"错误: 缺少 AI/视觉 依赖库 ({e.name})")
    print("=" * 60)
    print("请安装额外的视觉处理库:")
    print("  pip install opencv-python numpy ultralytics")
    sys.exit(1)

# GStreamer 依赖检查
try:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import GLib, Gst
except ImportError:
    print("错误: 未找到 GStreamer Python 绑定")
    sys.exit(1)

try:
    from gst_signalling.utils import find_producer_peer_id_by_name
except ImportError:
    print("错误: 未找到 gst_signalling 模块，请运行 pip install 'reachy-mini[gstreamer]'")
    sys.exit(1)


class GstVideoConsumer:
    """GStreamer WebRTC 视频流接收器 (带 YOLO 支持)"""

    def __init__(
        self,
        signalling_host: str,
        signalling_port: int,
        peer_name: str,
    ) -> None:
        print("=" * 60)
        print("Reachy Mini WebRTC + YOLO Object Detection")
        print("=" * 60)
        print(f"\n配置信息:")
        print(f"  信令服务器: {signalling_host}:{signalling_port}")
        print(f"  正在加载 YOLOv8 Nano 模型 (首次运行会自动下载)...")
        
        # 加载 YOLO 模型 (使用 nano 版本以保证 CPU 实时性)
        self.model = YOLO("yolov8n.pt") 
        print("  YOLO 模型加载完成")

        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("webRTC-consumer")
        self.source = Gst.ElementFactory.make("webrtcsrc")
        self.appsink = None  # 用于存储 appsink 引用

        if not self.pipeline or not self.source:
            print("错误: 无法创建 GStreamer 组件，请检查安装。")
            sys.exit(-1)

        self.pipeline.add(self.source)

        print(f"  正在连接到 {peer_name}...")
        try:
            peer_id = find_producer_peer_id_by_name(
                signalling_host, signalling_port, peer_name
            )
        except Exception as e:
            print(f"  连接信令服务器失败: {e}")
            sys.exit(1)
            
        print(f"  找到对等体 ID: {peer_id}")

        self.source.connect("pad-added", self.webrtcsrc_pad_added_cb)
        signaller = self.source.get_property("signaller")
        signaller.set_property("producer-peer-id", peer_id)
        signaller.set_property("uri", f"ws://{signalling_host}:{signalling_port}")

    def webrtcsrc_pad_added_cb(self, webrtcsrc: Gst.Element, pad: Gst.Pad) -> None:
        """当新流到达时的回调"""
        pad_name = pad.get_name()
        print(f"\n[新流] 检测到 {pad_name} 流")

        if pad_name.startswith("video"):
            print("  初始化 YOLO 视频处理管道...")
            
            # 创建处理链: videoconvert -> capsfilter -> appsink
            # videoconvert: 确保颜色空间转换
            # capsfilter: 强制转换为 OpenCV 需要的 BGR 格式
            # appsink: 允许 Python 代码提取帧
            
            convert = Gst.ElementFactory.make("videoconvert")
            capsfilter = Gst.ElementFactory.make("capsfilter")
            self.appsink = Gst.ElementFactory.make("appsink")

            if not all([convert, capsfilter, self.appsink]):
                print("  错误: 无法创建视频处理组件")
                return

            # 设置 appsink 属性
            self.appsink.set_property("emit-signals", True) # 发送信号（可选，这里我们用 pull）
            self.appsink.set_property("sync", False)        # 尽可能快地处理，避免缓冲区阻塞
            self.appsink.set_property("drop", True)         # 如果处理不过来，丢弃旧帧
            self.appsink.set_property("max-buffers", 1)     # 只保留最新的一帧

            # 强制输出为 BGR 格式 (OpenCV 默认格式)
            caps = Gst.Caps.from_string("video/x-raw, format=BGR")
            capsfilter.set_property("caps", caps)

            # 将组件加入管道
            self.pipeline.add(convert)
            self.pipeline.add(capsfilter)
            self.pipeline.add(self.appsink)

            # 链接: pad -> convert -> capsfilter -> appsink
            pad.link(convert.get_static_pad("sink"))
            convert.link(capsfilter)
            capsfilter.link(self.appsink)

            # 同步状态
            convert.sync_state_with_parent()
            capsfilter.sync_state_with_parent()
            self.appsink.sync_state_with_parent()
            
            # 配置 webrtcbin 延迟
            if isinstance(webrtcsrc, Gst.Bin):
                webrtcbin = webrtcsrc.get_by_name("webrtcbin0")
                if webrtcbin:
                    webrtcbin.set_property("latency", 0) # 实时检测需要最低延迟

            print("  视频处理管道已就绪!")

        elif pad_name.startswith("audio"):
            # 音频部分保持原样，直接播放
            sink = Gst.ElementFactory.make("autoaudiosink")
            if sink:
                self.pipeline.add(sink)
                pad.link(sink.get_static_pad("sink"))
                sink.sync_state_with_parent()
                print("  音频流已启动")

    def get_frame(self):
        """尝试从 appsink 获取最新一帧并转换为 OpenCV 图像"""
        if self.appsink is None:
            return None

        # 尝试拉取样本 (设置较小的超时时间，避免阻塞主循环)
        sample = self.appsink.emit("try-pull-sample", 5 * Gst.MSECOND)
        if sample is None:
            return None

        # 获取缓冲区
        buf = sample.get_buffer()
        caps = sample.get_caps()
        
        # 解析高度和宽度
        structure = caps.get_structure(0)
        height = structure.get_value("height")
        width = structure.get_value("width")

        # 将 GStreamer 缓冲区转换为 numpy 数组
        buffer = buf.extract_dup(0, buf.get_size())
        frame = np.ndarray((height, width, 3), buffer=buffer, dtype=np.uint8)
        
        return frame

    def play(self) -> None:
        self.pipeline.set_state(Gst.State.PLAYING)
        print("\n正在接收视频流并运行 YOLO... (按 'q' 或 Ctrl+C 退出)")

    def stop(self) -> None:
        print("\n正在停止...")
        self.pipeline.set_state(Gst.State.NULL)
        cv2.destroyAllWindows()

    def get_bus(self) -> Gst.Bus:
        return self.pipeline.get_bus()


def main() -> None:
    parser = argparse.ArgumentParser(description="Reachy Mini WebRTC + YOLO Demo")
    parser.add_argument("-s", "--signaling-host", default="127.0.0.1", help="Reachy IP")
    parser.add_argument("-p", "--signaling-port", type=int, default=8443, help="Port")
    parser.add_argument("-n", "--peer-name", default="reachymini", help="Peer Name")
    args = parser.parse_args()

    consumer = GstVideoConsumer(args.signaling_host, args.signaling_port, args.peer_name)
    consumer.play()

    bus = consumer.get_bus()
    
    try:
        while True:
            # 1. 处理 GStreamer 消息 (非阻塞)
            msg = bus.timed_pop_filtered(1 * Gst.MSECOND, Gst.MessageType.ANY)
            if msg:
                if msg.type == Gst.MessageType.ERROR:
                    err, debug = msg.parse_error()
                    print(f"Error: {err}, {debug}")
                    break
                elif msg.type == Gst.MessageType.EOS:
                    break
            
            # 2. 获取视频帧并处理
            frame = consumer.get_frame()
            if frame is not None:
                # --- YOLO 检测核心部分 ---
                
                # 运行推理 (stream=True 更高效，verbose=False 减少日志)
                results = consumer.model(frame, stream=True, verbose=False)

                # 绘制结果
                for result in results:
                    # plot() 方法直接在图像上画框，返回 BGR numpy 数组
                    annotated_frame = result.plot()
                    
                    # 显示图像
                    cv2.imshow("Reachy Mini - YOLOv8 Live", annotated_frame)
                
                # --- 结束检测部分 ---

            # 3. GUI 刷新与键盘控制
            # waitKey 对于 OpenCV 显示窗口是必须的
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        consumer.stop()

if __name__ == "__main__":
    main()