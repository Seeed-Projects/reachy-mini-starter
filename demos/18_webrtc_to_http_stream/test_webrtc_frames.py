#!/usr/bin/env python3
"""调试脚本：测试 WebRTC 帧接收"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import gi
gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst
from gst_signalling.utils import find_producer_peer_id_by_name

class WebRTCFrameTester:
    def __init__(self, signalling_host: str, signalling_port: int = 8443, peer_name: str = "reachymini"):
        self.signalling_host = signalling_host
        self.signalling_port = signalling_port
        self.peer_name = peer_name
        self.appsink = None
        self.frame_count = 0
        self.no_frame_count = 0

        Gst.init(None)
        print(f"[测试] 初始化 WebRTC 连接...")
        print(f"[测试] 信令服务器: ws://{signalling_host}:{signalling_port}")

        # 创建管道
        self.pipeline = Gst.Pipeline.new("test-pipeline")
        self.source = Gst.ElementFactory.make("webrtcsrc")

        if not self.pipeline or not self.source:
            print("[错误] 无法创建 GStreamer 元素")
            sys.exit(1)

        self.pipeline.add(self.source)

        # 连接信号
        self.source.connect("pad-added", self._on_pad_added)

        # 查找对等端
        try:
            peer_id = find_producer_peer_id_by_name(
                signalling_host, signalling_port, peer_name
            )
            print(f"[测试] 找到对等端 ID: {peer_id}")
        except Exception as e:
            print(f"[错误] 无法连接信令服务器: {e}")
            sys.exit(1)

        # 配置信令
        signaller = self.source.get_property("signaller")
        signaller.set_property("producer-peer-id", peer_id)
        signaller.set_property("uri", f"ws://{signalling_host}:{signalling_port}")

        print("[测试] WebRTC 管道设置完成")

    def _on_pad_added(self, webrtcsrc, pad):
        pad_name = pad.get_name()
        print(f"[测试] Pad 添加: {pad_name}")

        if pad_name.startswith("video"):
            print("[测试] 视频 pad 已连接!")
            # 创建转换元素
            convert = Gst.ElementFactory.make("videoconvert")
            capsfilter = Gst.ElementFactory.make("capsfilter")
            self.appsink = Gst.ElementFactory.make("appsink")

            if not convert or not capsfilter or not self.appsink:
                print("[错误] 无法创建视频处理元素")
                return

            # 设置输出格式为 BGR
            caps = Gst.Caps.from_string("video/x-raw, format=BGR")
            capsfilter.set_property("caps", caps)

            # 配置 appsink
            self.appsink.set_property("emit-signals", True)
            self.appsink.set_property("sync", False)
            self.appsink.set_property("max-buffers", 1)
            self.appsink.set_property("drop", True)

            # 添加到管道
            self.pipeline.add(convert)
            self.pipeline.add(capsfilter)
            self.pipeline.add(self.appsink)

            # 连接元素
            if not pad.link(convert.get_static_pad("sink")) == Gst.PadLinkReturn.OK:
                print("[错误] 无法链接 pad 到 convert")
                return
            if not convert.link(capsfilter) == Gst.PadLinkReturn.OK:
                print("[错误] 无法链接 convert 到 capsfilter")
                return
            if not capsfilter.link(self.appsink) == Gst.PadLinkReturn.OK:
                print("[错误] 无法链接 capsfilter 到 appsink")
                return

            # 同步状态
            convert.sync_state_with_parent()
            capsfilter.sync_state_with_parent()
            self.appsink.sync_state_with_parent()

            print("[测试] 视频管道已建立")

    def test_frames(self, duration: int = 10):
        """测试帧接收"""
        print(f"[测试] 启动管道，测试 {duration} 秒...")

        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("[错误] 无法启动管道")
            return

        start_time = time.time()
        last_frame_time = start_time

        while time.time() - start_time < duration:
            if self.appsink:
                sample = self.appsink.emit("try-pull-sample", 10 * Gst.MSECOND)

                if sample:
                    self.frame_count += 1
                    self.no_frame_count = 0
                    last_frame_time = time.time()

                    buf = sample.get_buffer()
                    caps = sample.get_caps()
                    structure = caps.get_structure(0)
                    width = structure.get_value("width")
                    height = structure.get_value("height")

                    if self.frame_count <= 5 or self.frame_count % 30 == 0:
                        print(f"[帧] #{self.frame_count}: {width}x{height}, 大小: {buf.get_size()} bytes")
                else:
                    self.no_frame_count += 1
                    if self.no_frame_count <= 3 or self.no_frame_count % 50 == 0:
                        print(f"[等待] 无帧数据 ({self.no_frame_count} 次)")

            time.sleep(0.1)

        elapsed = time.time() - start_time
        print(f"\n[结果] 测试完成:")
        print(f"  - 总帧数: {self.frame_count}")
        print(f"  - 帧率: {self.frame_count / elapsed:.2f} FPS")
        print(f"  - 最后收到帧: {time.time() - last_frame_time:.2f} 秒前")

        if self.frame_count == 0:
            print("\n[警告] 没有收到任何帧!")
            print("可能的原因:")
            print("  1. 机器人端的 WebRTC 生产者没有发送视频")
            print("  2. 网络连接问题")
            print("  3. GStreamer 管道配置问题")

        self.pipeline.set_state(Gst.State.NULL)


def main():
    parser = argparse.ArgumentParser(description="测试 WebRTC 帧接收")
    parser.add_argument("-s", "--signaling-host", default="10.42.0.75", help="信令服务器地址")
    parser.add_argument("-p", "--signaling-port", type=int, default=8443, help="信令服务器端口")
    parser.add_argument("-n", "--peer-name", default="reachymini", help="对等端名称")
    parser.add_argument("-d", "--duration", type=int, default=10, help="测试时长（秒）")
    args = parser.parse_args()

    tester = WebRTCFrameTester(args.signaling_host, args.signaling_port, args.peer_name)
    tester.test_frames(args.duration)


if __name__ == "__main__":
    main()
