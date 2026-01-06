#!/usr/bin/env python3
"""Reachy Mini: YOLO 视觉检测 + Zenoh 实时控制

功能:
1. 视频流: 使用 GStreamer WebRTC 接收 (命令行参数)。
2. 机器人控制: 使用 Zenoh 协议 (配置文件 robot_ip)，实现超低延迟控制。
"""

import argparse
import sys
import time
import threading
import json
import math
import numpy as np
from pathlib import Path

# ---------------------- 路径配置 ----------------------
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config_loader import get_config
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    try:
        from config_loader import get_config
    except ImportError:
        print("错误: 无法找到 config_loader.py")
        sys.exit(1)

# ---------------------- 依赖检查 ----------------------
try:
    import zenoh
except ImportError:
    print("错误: 请安装 zenoh 库 (pip install zenoh)")
    sys.exit(1)

try:
    import cv2
    from ultralytics import YOLO
except ImportError:
    print("错误: 请安装 opencv-python 和 ultralytics")
    sys.exit(1)

try:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import GLib, Gst
    from gst_signalling.utils import find_producer_peer_id_by_name
except ImportError:
    print("错误: 未找到 GStreamer 或 reachy-mini 相关库")
    sys.exit(1)


class ZenohRobotController:
    """基于 Zenoh 的机器人运动控制类"""
    
    def __init__(self):
        # 1. 读取配置
        try:
            config = get_config()
            self.robot_ip = config.robot_ip
            self.zenoh_port = "7447" # Zenoh 默认端口
        except Exception as e:
            print(f"[错误] 读取配置文件失败: {e}")
            sys.exit(1)
        
        self.topic_command = "reachy_mini/command"
        self.current_yaw_deg = 0.0 # 内部状态维护使用角度 (更直观)
        self.lock = threading.Lock()
        
        print("-" * 40)
        print(f"[控制] Zenoh 连接目标: tcp/{self.robot_ip}:{self.zenoh_port}")
        print("-" * 40)
        
        # 2. 初始化 Zenoh
        self.session = None
        self.pub = None
        self._init_zenoh()
        
        # 3. 启用电机
        self.set_torque(True)

    def _init_zenoh(self):
        try:
            conf = zenoh.Config()
            # 点对点连接配置
            conf.insert_json5("connect/endpoints", f"['tcp/{self.robot_ip}:{self.zenoh_port}']")
            self.session = zenoh.open(conf)
            self.pub = self.session.declare_publisher(self.topic_command)
            print("[控制] ✅ Zenoh 会话已建立")
        except Exception as e:
            print(f"[错误] Zenoh 连接失败: {e}")
            sys.exit(1)

    def set_torque(self, state: bool):
        """设置电机扭矩状态"""
        cmd = {"torque": state, "ids": None}
        self._send_json(cmd)
        if state:
            print("[控制] 电机已启用 (Torque ON)")
        else:
            print("[控制] 电机已放松 (Torque OFF)")

    def move_yaw_relative(self, delta_deg: float):
        """相对移动偏航角 (输入为角度，自动转弧度发送)"""
        target_deg = self.current_yaw_deg + delta_deg
        
        # 限制角度范围 [-160, 160]
        target_deg = max(-160, min(160, target_deg))
        
        if target_deg == self.current_yaw_deg:
            return

        self.current_yaw_deg = target_deg
        
        # 转换为弧度 (Zenoh 协议通常使用弧度)
        # 1 度 ≈ 0.01745 弧度
        target_rad = math.radians(self.current_yaw_deg)
        
        # 发送指令
        self._send_json({"body_yaw": target_rad})

    def reset_position(self):
        """回正"""
        self.current_yaw_deg = 0.0
        self._send_json({"body_yaw": 0.0})

    def _send_json(self, data: dict):
        """发送 JSON 指令 (非阻塞)"""
        # Zenoh put 操作非常快，通常不需要像 HTTP 那样开线程
        # 但为了绝对不影响视频渲染，我们还是简单地用线程抛出
        def _do_put():
            if self.pub:
                self.pub.put(json.dumps(data))
        
        threading.Thread(target=_do_put, daemon=True).start()

    def close(self):
        """清理资源"""
        if self.session:
            print("[控制] 正在关闭 Zenoh...")
            self.set_torque(False) # 退出时放松电机
            time.sleep(0.2)
            self.session.close()


class GstVideoConsumer:
    """GStreamer WebRTC 视频流接收器 (保持不变)"""

    def __init__(self, signalling_host: str, signalling_port: int, peer_name: str) -> None:
        Gst.init(None)
        print(f"[视觉] 加载 YOLOv8n 模型...")
        self.model = YOLO("yolov8n.pt") 
        
        print(f"[视觉] 初始化 GStreamer WebRTC...")
        self.pipeline = Gst.Pipeline.new("webRTC-consumer")
        self.source = Gst.ElementFactory.make("webrtcsrc")
        self.appsink = None

        if not self.pipeline or not self.source:
            print("错误: 无法创建 GStreamer 管道")
            sys.exit(1)

        self.pipeline.add(self.source)

        try:
            print(f"[视觉] 连接信令: {signalling_host}:{signalling_port}")
            peer_id = find_producer_peer_id_by_name(signalling_host, signalling_port, peer_name)
        except Exception as e:
            print(f"[错误] 无法连接信令服务器: {e}")
            sys.exit(1)

        self.source.connect("pad-added", self.webrtcsrc_pad_added_cb)
        signaller = self.source.get_property("signaller")
        signaller.set_property("producer-peer-id", peer_id)
        signaller.set_property("uri", f"ws://{signalling_host}:{signalling_port}")

    def webrtcsrc_pad_added_cb(self, webrtcsrc, pad):
        pad_name = pad.get_name()
        if pad_name.startswith("video"):
            print("[视觉] 视频流已连接")
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
            
            if isinstance(webrtcsrc, Gst.Bin):
                webrtcbin = webrtcsrc.get_by_name("webrtcbin0")
                if webrtcbin: webrtcbin.set_property("latency", 0)

        elif pad_name.startswith("audio"):
            sink = Gst.ElementFactory.make("autoaudiosink")
            self.pipeline.add(sink)
            pad.link(sink.get_static_pad("sink"))
            sink.sync_state_with_parent()

    def get_frame(self):
        if self.appsink is None: return None
        sample = self.appsink.emit("try-pull-sample", 5 * Gst.MSECOND)
        if sample is None: return None
        
        buf = sample.get_buffer()
        caps = sample.get_caps()
        h = caps.get_structure(0).get_value("height")
        w = caps.get_structure(0).get_value("width")
        arr = np.ndarray((h, w, 3), buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        return arr

    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)


def main():
    # 参数解析 (仅视频流配置)
    parser = argparse.ArgumentParser(description="Reachy Mini WebRTC + YOLO + Zenoh Control")
    parser.add_argument("-s", "--signaling-host", default="127.0.0.1", help="Reachy IP for Video")
    parser.add_argument("-p", "--signaling-port", type=int, default=8443, help="Port for Video")
    parser.add_argument("-n", "--peer-name", default="reachymini", help="Peer Name")
    args = parser.parse_args()

    # 1. 启动视频
    consumer = GstVideoConsumer(args.signaling_host, args.signaling_port, args.peer_name)
    consumer.play()

    # 2. 启动 Zenoh 控制
    try:
        controller = ZenohRobotController()
    except SystemExit:
        consumer.stop()
        return

    print("\n" + "="*60)
    print("🎮 Zenoh 极速控制模式:")
    print("  [A] 向左微调 (实时)")
    print("  [D] 向右微调 (实时)")
    print("  [S] 回正")
    print("  [Q] 退出")
    print("="*60 + "\n")

    bus = consumer.pipeline.get_bus()
    
    # 控制步进角度 (度)
    # Zenoh 响应很快，可以设置小一点实现平滑
    STEP_ANGLE_DEG = 1.0  

    try:
        while True:
            # GStreamer 消息处理
            msg = bus.timed_pop_filtered(1 * Gst.MSECOND, Gst.MessageType.ERROR | Gst.MessageType.EOS)
            if msg:
                if msg.type == Gst.MessageType.ERROR:
                    print("GStreamer Error")
                    break
            
            # 视频帧处理
            frame = consumer.get_frame()
            if frame is not None:
                results = consumer.model(frame, stream=True, verbose=False)
                for res in results:
                    annotated_frame = res.plot()
                    
                    # 显示当前角度
                    text = f"Yaw: {controller.current_yaw_deg:.1f} deg"
                    cv2.putText(annotated_frame, text, (20, 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    cv2.imshow("Reachy Mini Zenoh Control", annotated_frame)

            # 键盘输入
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('a'):
                controller.move_yaw_relative(STEP_ANGLE_DEG)
            elif key == ord('d'):
                controller.move_yaw_relative(-STEP_ANGLE_DEG)
            elif key == ord('s'):
                controller.reset_position()

    except KeyboardInterrupt:
        pass
    finally:
        print("\n正在停止...")
        controller.close()
        consumer.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()