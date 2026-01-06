#!/usr/bin/env python3
"""Reachy Mini: YOLO 视觉检测 + Zenoh 头部/身体双控 (修复版)

修复说明:
1. 修复 set_torque 方法: 增加 "ids": None 字段，防止服务端崩溃。
2. 保持 Spec 3.3 协议兼容: 头部使用矩阵控制，身体使用弧度控制。
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
    # 尝试递归查找
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
    """基于 Zenoh 的机器人运动控制类 (修复 KeyError: 'ids')"""
    
    def __init__(self):
        # 1. 读取配置
        try:
            config = get_config()
            self.robot_ip = config.robot_ip
            self.zenoh_port = "7447" 
        except Exception as e:
            print(f"[错误] 读取配置文件失败: {e}")
            sys.exit(1)
        
        self.topic_command = "reachy_mini/command"
        
        # 状态记录 (角度制，方便计算)
        self.current_body_yaw_deg = 0.0
        self.current_head_yaw_deg = 0.0
        
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
            # 客户端模式连接
            conf.insert_json5("connect/endpoints", f"['tcp/{self.robot_ip}:{self.zenoh_port}']")
            conf.insert_json5("mode", "'client'")
            
            self.session = zenoh.open(conf)
            self.pub = self.session.declare_publisher(self.topic_command)
            print("[控制] ✅ Zenoh 会话已建立")
        except Exception as e:
            print(f"[错误] Zenoh 连接失败: {e}")
            sys.exit(1)

    def set_torque(self, state: bool):
        """设置电机扭矩 (修复版)"""
        # --- 关键修复 ---
        # 服务端代码要求必须存在 "ids" 键，否则会报 KeyError
        cmd = {
            "torque": state,
            "ids": None  # 必须显式加上这一项
        }
        self._send_json(cmd)
        print(f"[控制] 电机状态指令已发送: {'ON' if state else 'OFF'}")

    def move_body_relative(self, delta_deg: float):
        """控制身体旋转 (发送 float 弧度)"""
        target = self.current_body_yaw_deg + delta_deg
        # 身体限制: ±160度
        target = max(-160, min(160, target))
        
        if target == self.current_body_yaw_deg:
            return
            
        self.current_body_yaw_deg = target
        
        # 转换为弧度
        rad = math.radians(target)
        self._send_json({"body_yaw": rad})

    def move_head_relative(self, delta_deg: float):
        """控制头部旋转 (发送 4x4 矩阵)"""
        target = self.current_head_yaw_deg + delta_deg
        # 头部限制: 范围小一些，设为 ±50度
        target = max(-50, min(50, target))
        
        if target == self.current_head_yaw_deg:
            return
            
        self.current_head_yaw_deg = target
        
        # 1. 计算弧度
        rad = math.radians(target)
        
        # 2. 构建 4x4 旋转矩阵 (绕 Z 轴旋转)
        c = math.cos(rad)
        s = math.sin(rad)
        
        # 标准旋转矩阵 Rz
        matrix = [
            [c, -s, 0.0, 0.0],
            [s,  c, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]
        
        self._send_json({"head_pose": matrix})

    def reset_position(self):
        """全部归位"""
        self.current_body_yaw_deg = 0.0
        self.current_head_yaw_deg = 0.0
        
        # 头部归位矩阵 (单位矩阵)
        identity_matrix = [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ]
        
        cmd = {
            "body_yaw": 0.0,
            "head_pose": identity_matrix
        }
        self._send_json(cmd)

    def _send_json(self, data: dict):
        """发送 JSON 指令"""
        def _do_put():
            if self.pub:
                # 序列化 json
                json_str = json.dumps(data)
                self.pub.put(json_str)
        
        # 使用线程发送，确保不阻塞视频渲染
        threading.Thread(target=_do_put, daemon=True).start()

    def close(self):
        if self.session:
            print("[控制] 正在断开连接...")
            # 退出时也必须带上 ids: None
            cmd = {"torque": False, "ids": None}
            self._send_json(cmd)
            time.sleep(0.2)
            self.session.close()


class GstVideoConsumer:
    """GStreamer 视频流接收 (保持不变)"""

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
            peer_id = find_producer_peer_id_by_name(signalling_host, signalling_port, peer_name)
        except Exception:
            print(f"[错误] 无法连接信令服务器，请检查 IP: {signalling_host}")
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
                web = webrtcsrc.get_by_name("webrtcbin0")
                if web: web.set_property("latency", 0)

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
    parser = argparse.ArgumentParser(description="Reachy Mini Zenoh Dual Control")
    parser.add_argument("-s", "--signaling-host", default="127.0.0.1", help="Video IP")
    parser.add_argument("-p", "--signaling-port", type=int, default=8443, help="Video Port")
    parser.add_argument("-n", "--peer-name", default="reachymini", help="Peer Name")
    args = parser.parse_args()

    # 1. 启动视频
    consumer = GstVideoConsumer(args.signaling_host, args.signaling_port, args.peer_name)
    consumer.play()

    # 2. 启动控制 (自动读取 config)
    try:
        controller = ZenohRobotController()
    except SystemExit:
        consumer.stop()
        return

    print("\n" + "="*60)
    print("🎮 双模控制指南:")
    print("  [A / D] 身体旋转 (大范围)")
    print("  [H / L] 头部旋转 (小范围, 独立)")
    print("  [S]     全部回正")
    print("  [Q]     退出")
    print("="*60 + "\n")

    bus = consumer.pipeline.get_bus()
    
    # 步进参数
    BODY_STEP = 1.5  # 身体每次 1.5度
    HEAD_STEP = 1.0  # 头部每次 1.0度 (更精细)

    try:
        while True:
            msg = bus.timed_pop_filtered(1 * Gst.MSECOND, Gst.MessageType.ERROR | Gst.MessageType.EOS)
            if msg:
                if msg.type == Gst.MessageType.ERROR:
                    print("Video Error")
                    break
            
            frame = consumer.get_frame()
            if frame is not None:
                results = consumer.model(frame, stream=True, verbose=False)
                for res in results:
                    annotated_frame = res.plot()
                    
                    # 界面显示双重状态
                    info_text = f"Body: {controller.current_body_yaw_deg:.1f} | Head: {controller.current_head_yaw_deg:.1f}"
                    cv2.putText(annotated_frame, info_text, (20, 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    
                    cv2.imshow("Reachy Mini Dual Control", annotated_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            # 身体控制
            elif key == ord('a'):
                controller.move_body_relative(BODY_STEP)
            elif key == ord('d'):
                controller.move_body_relative(-BODY_STEP)
            # 头部控制
            elif key == ord('h'):
                controller.move_head_relative(HEAD_STEP) # 顺时针/左
            elif key == ord('l'):
                controller.move_head_relative(-HEAD_STEP) # 逆时针/右
            # 回正
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