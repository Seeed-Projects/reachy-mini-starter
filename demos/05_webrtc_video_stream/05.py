#!/usr/bin/env python3
"""Reachy Mini WebRTC 视频流接收演示

使用 GStreamer WebRTC 接收 Reachy Mini 的视频和音频流
需要安装 GStreamer 和 WebRTC 插件（参考 README.md）
"""

import argparse
import sys
from pathlib import Path

# 尝试导入 GStreamer，如果失败则给出友好的错误提示
try:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import GLib, Gst  # noqa: E402
except ImportError:
    print("=" * 60)
    print("错误: 未找到 GStreamer Python 绑定")
    print("=" * 60)
    print("\n请按照以下步骤安装:")
    print("1. 查看 README.md 中的 GStreamer 安装指南")
    print("2. 或访问: docs/GSTREAMER_CN.md (中文) / docs/GSTREAMER.md (English)")
    print("\n快速安装 (Ubuntu):")
    print("  sudo apt-get install libgstreamer1.0-dev python3-gi")
    print("\n还需要安装 WebRTC 插件，详见文档。")
    sys.exit(1)

try:
    from gst_signalling.utils import find_producer_peer_id_by_name
except ImportError:
    print("=" * 60)
    print("错误: 未找到 gst_signalling 模块")
    print("=" * 60)
    print("\n请安装 reachy-mini 包的 gstreamer 额外依赖:")
    print("  uv pip install 'reachy-mini[gstreamer]'")
    print("  或")
    print("  pip install 'reachy-mini[gstreamer]'")
    sys.exit(1)


class GstVideoConsumer:
    """GStreamer WebRTC 视频流接收器"""

    def __init__(
        self,
        signalling_host: str,
        signalling_port: int,
        peer_name: str,
    ) -> None:
        """初始化 WebRTC 消费者

        Args:
            signalling_host: 信令服务器地址 (Reachy Mini 的 IP)
            signalling_port: 信令服务器端口 (默认 8443)
            peer_name: 对等体名称 (默认 "reachymini")
        """
        print("=" * 60)
        print("Reachy Mini WebRTC 视频流接收")
        print("=" * 60)
        print(f"\n配置信息:")
        print(f"  信令服务器: {signalling_host}:{signalling_port}")
        print(f"  对等体名称: {peer_name}")
        print(f"  正在初始化 GStreamer...")

        Gst.init(None)

        self.pipeline = Gst.Pipeline.new("webRTC-consumer")
        self.source = Gst.ElementFactory.make("webrtcsrc")

        if not self.pipeline:
            print("错误: 无法创建 GStreamer 管道")
            sys.exit(-1)

        if not self.source:
            print("错误: 无法创建 webrtcsrc 组件")
            print("\n请确保已安装 WebRTC 插件:")
            print("  查看 README.md 或 docs/GSTREAMER*.md 获取安装指南")
            print("\  插件源码: https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc")
            sys.exit(-1)

        self.pipeline.add(self.source)

        print(f"  正在连接到 {peer_name}...")
        peer_id = find_producer_peer_id_by_name(
            signalling_host, signalling_port, peer_name
        )
        print(f"  找到对等体 ID: {peer_id}")

        self.source.connect("pad-added", self.webrtcsrc_pad_added_cb)
        signaller = self.source.get_property("signaller")
        signaller.set_property("producer-peer-id", peer_id)
        signaller.set_property("uri", f"ws://{signalling_host}:{signalling_port}")

    def dump_latency(self) -> None:
        """打印当前管道延迟"""
        query = Gst.Query.new_latency()
        self.pipeline.query(query)
        latency_min, latency_live, latency_max = query.parse_latency()
        print(f"[延迟] 管道延迟 - 最小: {latency_min}us, 实时: {latency_live}, 最大: {latency_max}us")

    def _configure_webrtcbin(self, webrtcsrc: Gst.Element) -> None:
        """配置 WebRTC bin 的延迟参数"""
        if isinstance(webrtcsrc, Gst.Bin):
            webrtcbin_name = "webrtcbin0"
            webrtcbin = webrtcsrc.get_by_name(webrtcbin_name)
            if webrtcbin is not None:
                # jitterbuffer 默认 200ms 缓冲，我们降低到 50ms 以减少延迟
                webrtcbin.set_property("latency", 50)
                print(f"  WebRTC 延迟设置为: 50ms")

    def webrtcsrc_pad_added_cb(self, webrtcsrc: Gst.Element, pad: Gst.Pad) -> None:
        """当新 pad 添加时的回调处理"""
        self._configure_webrtcbin(webrtcsrc)

        pad_name = pad.get_name()
        print(f"\n[新流] 检测到 {pad_name} 流")

        if pad_name.startswith("video"):  # type: ignore[union-attr]
            # webrtcsrc 自动解码并转换视频
            print("  创建视频显示 (fps-displaysink)...")
            sink = Gst.ElementFactory.make("fpsdisplaysink")
            if sink is None:
                print("  警告: fpsdisplaysink 不可用，尝试使用 autovideosink")
                sink = Gst.ElementFactory.make("autovideosink")

            if sink is None:
                print("  错误: 无法创建视频输出设备")
                return

            self.pipeline.add(sink)
            pad.link(sink.get_static_pad("sink"))  # type: ignore[arg-type]
            sink.sync_state_with_parent()
            print("  视频流已启动!")

        elif pad_name.startswith("audio"):  # type: ignore[union-attr]
            # webrtcsrc 自动解码并转换音频
            print("  创建音频输出 (autoaudiosink)...")
            sink = Gst.ElementFactory.make("autoaudiosink")
            if sink is None:
                print("  警告: 无法创建音频输出设备")
                return

            self.pipeline.add(sink)
            pad.link(sink.get_static_pad("sink"))  # type: ignore[arg-type]
            sink.sync_state_with_parent()
            print("  音频流已启动!")

        # 每 5 秒打印一次延迟信息
        GLib.timeout_add_seconds(5, self.dump_latency)

    def __del__(self) -> None:
        """析构函数，清理 GStreamer 资源"""
        Gst.deinit()

    def get_bus(self) -> Gst.Bus:
        """获取 GStreamer 总线"""
        return self.pipeline.get_bus()

    def play(self) -> None:
        """启动 GStreamer 管道"""
        print("\n" + "=" * 60)
        print("启动视频流接收...")
        print("=" * 60)
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("错误: 启动播放失败")
            sys.exit(-1)
        print("\n正在接收视频流... (按 Ctrl+C 退出)")

    def stop(self) -> None:
        """停止 GStreamer 管道"""
        print("\n正在停止...")
        self.pipeline.send_event(Gst.Event.new_eos())
        self.pipeline.set_state(Gst.State.NULL)
        print("已停止")


def process_msg(bus: Gst.Bus, pipeline: Gst.Pipeline) -> bool:
    """处理 GStreamer 总线消息"""
    msg = bus.timed_pop_filtered(10 * Gst.MSECOND, Gst.MessageType.ANY)
    if msg:
        if msg.type == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            print(f"\n[错误] {err}, {debug}")
            return False
        elif msg.type == Gst.MessageType.EOS:
            print("\n[信息] 流结束")
            return False
        elif msg.type == Gst.MessageType.LATENCY:
            if pipeline:
                try:
                    pipeline.recalculate_latency()
                except Exception as e:
                    print(f"[警告] 重新计算延迟失败: {e}")
        elif msg.type == Gst.MessageType.WARNING:
            warning, debug = msg.parse_warning()
            print(f"\n[警告] {warning}")
            if debug:
                print(f"  详情: {debug}")
    return True


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reachy Mini WebRTC 视频流接收演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 05.py                          # 使用默认配置 (127.0.0.1:8443)
  python3 05.py --signaling-host 10.42.0.75  # 指定 Reachy Mini IP
  python3 05.py -s 192.168.1.100 -p 8443    # 完整配置

环境:
  确保已安装 GStreamer 和 WebRTC 插件
  查看 README.md 获取安装指南
        """
    )
    parser.add_argument(
        "-s", "--signaling-host",
        default="127.0.0.1",
        help="GStreamer 信令服务器地址 (Reachy Mini IP 地址)"
    )
    parser.add_argument(
        "-p", "--signaling-port",
        type=int,
        default=8443,
        help="GStreamer 信令服务器端口 (默认: 8443)"
    )
    parser.add_argument(
        "-n", "--peer-name",
        default="reachymini",
        help="对等体名称 (默认: reachymini)"
    )

    args = parser.parse_args()

    try:
        consumer = GstVideoConsumer(
            args.signaling_host,
            args.signaling_port,
            args.peer_name,
        )
        consumer.play()

        # 等待错误或 EOS
        bus = consumer.get_bus()
        try:
            while True:
                if not process_msg(bus, consumer.pipeline):
                    break

        except KeyboardInterrupt:
            print("\n\n用户中断")
        finally:
            consumer.stop()

    except Exception as e:
        print(f"\n错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
