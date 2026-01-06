#!/usr/bin/env python3
"""Linux 下使用 PulseAudio 将系统音频推流到 Reachy Mini

这个脚本使用 PulseAudio 的 monitor device 捕获系统音频，
并通过 UDP 推流到 Reachy Mini 播放。

运行方式:
    python3 stream_pc_audio_pulse.py --robot-ip 10.42.0.75

依赖:
    sudo apt-get install pulseaudio-utils pulseaudio
    pip install numpy requests

或者使用 ffmpeg:
    sudo apt-get install ffmpeg
"""

import argparse
import logging
import socket
import subprocess
import sys
import time
from typing import Optional

import requests


# 配置
class StreamConfig:
    """推流配置."""

    SAMPLE_RATE = 48000
    CHANNELS = 1
    CHUNK_SIZE = 960  # 20ms @ 48kHz
    UDP_PORT = 5001
    API_PORT = 8001


class PulseAudioStreamer:
    """使用 PulseAudio 的音频推流器."""

    def __init__(self, robot_ip: str):
        """初始化推流器.

        Args:
            robot_ip: Reachy Mini 的 IP 地址
        """
        self._logger = logging.getLogger(__name__)
        self._robot_ip = robot_ip
        self._api_url = f"http://{robot_ip}:{StreamConfig.API_PORT}"
        self._ffmpeg_process = None

    def list_pulseaudio_sources(self) -> None:
        """列出所有 PulseAudio 音频源."""
        print("\nPulseAudio 音频源:")
        print("=" * 60)

        try:
            result = subprocess.run(
                ["pactl", "list", "sources"],
                capture_output=True,
                text=True,
                check=True
            )

            # 解析输出
            lines = result.stdout.split('\n')
            current_source = {}
            source_count = 0

            for line in lines:
                line = line.strip()
                if line.startswith("Name:"):
                    if current_source:
                        self._print_source(current_source)
                        source_count += 1
                    current_source = {"name": line.split(":", 1)[1].strip()}
                elif line.startswith("Description:"):
                    current_source["description"] = line.split(":", 1)[1].strip()
                elif line.startswith("device.description"):
                    current_source["device"] = line.split("=", 1)[1].strip().strip('"')

            # 打印最后一个
            if current_source:
                self._print_source(current_source)
                source_count += 1

            if source_count == 0:
                print("未找到任何音频源")

        except subprocess.CalledProcessError as e:
            print(f"错误: {e}")
            print("请确保已安装 PulseAudio:")
            print("  sudo apt-get install pulseaudio pulseaudio-utils")
        except FileNotFoundError:
            print("错误: 未找到 pactl 命令")
            print("请安装 PulseAudio:")
            print("  sudo apt-get install pulseaudio-utils")

        print("=" * 60)
        print("\n提示:")
        print("  - 带 '.monitor' 后缀的是可以捕获系统音频的设备")
        print("  - 使用 ffmpeg 方式需要指定完整的 PulseAudio 源名称")
        print()

    def _print_source(self, source: dict) -> None:
        """打印音频源信息."""
        name = source.get("name", "未知")
        desc = source.get("description", source.get("device", ""))
        is_monitor = ".monitor" in name

        marker = " 🔹 [推荐]" if is_monitor else ""
        print(f"  {name}{marker}")
        if desc:
            print(f"      描述: {desc}")
        print()

    def _start_stream_receiver(self) -> bool:
        """启动 Reachy Mini 上的 PCM 流接收服务.

        Returns:
            是否成功启动
        """
        self._logger.info(f"正在启动 {self._robot_ip} 上的 PCM 流接收服务...")

        try:
            # 先停止已有的流
            try:
                requests.post(f"{self._api_url}/stream/stop", timeout=5)
            except:
                pass

            # 启动新的 PCM 流接收 (使用 start_pcm 端点)
            data = {
                "port": StreamConfig.UDP_PORT,
                "sample_rate": StreamConfig.SAMPLE_RATE,
                "channels": StreamConfig.CHANNELS,
            }
            response = requests.post(
                f"{self._api_url}/stream/start_pcm",
                json=data,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            self._logger.info(f"✅ PCM 流接收服务已启动: {result}")
            return True

        except requests.exceptions.ConnectionError:
            self._logger.error(f"❌ 无法连接到 {self._api_url}")
            self._logger.error("请确认:")
            self._logger.error("  1. Reachy Mini 已开机")
            self._logger.error("  2. audio_stream_server.py 已在 Reachy Mini 上运行")
            return False
        except Exception as e:
            self._logger.error(f"启动流接收服务失败: {e}")
            return False

    def _stop_stream_receiver(self) -> None:
        """停止 Reachy Mini 上的流接收服务."""
        try:
            requests.post(f"{self._api_url}/stream/stop", timeout=5)
            self._logger.info("流接收服务已停止")
        except:
            pass

    def start_streaming_ffmpeg(self, source_name: Optional[str] = None) -> None:
        """使用 ffmpeg 开始音频推流.

        Args:
            source_name: PulseAudio 源名称，None 则自动查找 monitor
        """
        # 启动流接收服务
        if not self._start_stream_receiver():
            return

        # 查找 monitor 源
        if source_name is None:
            source_name = self._find_monitor_source()
            if source_name is None:
                print("\n⚠️  未找到 monitor 源")
                print("请运行 --list-sources 查看可用源")
                print("然后使用 --source SOURCE_NAME 指定")
                self._stop_stream_receiver()
                return

        print(f"\n使用音频源: {source_name}")
        print("开始推流...")
        print("按 Ctrl+C 停止\n")

        # ffmpeg 命令
        # 从 PulseAudio 捕获音频，转换为 PCM，通过 UDP 发送
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "warning",
            "-f", "pulse",
            "-i", source_name,
            "-f", "s16le",
            "-ar", str(StreamConfig.SAMPLE_RATE),
            "-ac", str(StreamConfig.CHANNELS),
            "-",
        ]

        try:
            # 启动 ffmpeg
            self._ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                bufsize=0  # 无缓冲
            )

            # 创建 UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            packet_count = 0
            start_time = time.time()

            # 读取并发送音频数据
            while True:
                data = self._ffmpeg_process.stdout.read(
                    StreamConfig.CHUNK_SIZE * 2  # 16-bit = 2 bytes
                )

                if not data:
                    break

                sock.sendto(data, (self._robot_ip, StreamConfig.UDP_PORT))

                packet_count += 1
                if packet_count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = packet_count / elapsed
                    print(f"推流中... {rate:.1f} packet/s    \r", end="", flush=True)

        except KeyboardInterrupt:
            print("\n\n用户中断")
        except FileNotFoundError:
            print("错误: 未找到 ffmpeg")
            print("请安装: sudo apt-get install ffmpeg")
        except Exception as e:
            print(f"\n推流错误: {e}")
        finally:
            if self._ffmpeg_process:
                self._ffmpeg_process.terminate()
                self._ffmpeg_process.wait()
            self._stop_stream_receiver()
            print("推流已停止")

    def _find_monitor_source(self) -> Optional[str]:
        """查找 PulseAudio monitor 源.

        Returns:
            源名称，如果找不到则返回 None
        """
        try:
            result = subprocess.run(
                ["pactl", "list", "sources"],
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith("Name:") and ".monitor" in line:
                    return line.split(":", 1)[1].strip()

        except Exception as e:
            self._logger.warning(f"查找 monitor 源失败: {e}")

        return None

    def start_streaming_parec(self) -> None:
        """使用 parec 命令开始音频推流 (更简单但无格式转换)."""
        # 启动流接收服务
        if not self._start_stream_receiver():
            return

        # 查找 monitor 源
        source_name = self._find_monitor_source()
        if source_name is None:
            print("\n⚠️  未找到 monitor 源")
            self._stop_stream_receiver()
            return

        print(f"\n使用音频源: {source_name}")
        print("开始推流...")
        print("按 Ctrl+C 停止\n")

        # parec 命令 - 直接从 PulseAudio 捕获
        cmd = [
            "parec",
            "-d", source_name,
            "--rate", str(StreamConfig.SAMPLE_RATE),
            "--channels", str(StreamConfig.CHANNELS),
            "--format", "s16le"
        ]

        try:
            # 启动 parec
            self._ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                bufsize=0
            )

            # 创建 UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            packet_count = 0
            start_time = time.time()

            # 读取并发送音频数据
            while True:
                data = self._ffmpeg_process.stdout.read(
                    StreamConfig.CHUNK_SIZE * 2  # 16-bit = 2 bytes
                )

                if not data:
                    break

                sock.sendto(data, (self._robot_ip, StreamConfig.UDP_PORT))

                packet_count += 1
                if packet_count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = packet_count / elapsed
                    print(f"推流中... {rate:.1f} packet/s    \r", end="", flush=True)

        except KeyboardInterrupt:
            print("\n\n用户中断")
        except FileNotFoundError:
            print("错误: 未找到 parec 命令")
            print("请安装: sudo apt-get install pulseaudio-utils")
        except Exception as e:
            print(f"\n推流错误: {e}")
        finally:
            if self._ffmpeg_process:
                self._ffmpeg_process.terminate()
                self._ffmpeg_process.wait()
            self._stop_stream_receiver()
            print("推流已停止")


def main():
    """主函数."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

    parser = argparse.ArgumentParser(
        description="Linux 下使用 PulseAudio 将系统音频推流到 Reachy Mini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出可用的音频源
  python3 stream_pc_audio_pulse.py --list-sources

  # 自动推流 (使用 ffmpeg)
  python3 stream_pc_audio_pulse.py --robot-ip 10.42.0.75

  # 自动推流 (使用 parec，更简单)
  python3 stream_pc_audio_pulse.py --robot-ip 10.42.0.75 --parec

  # 指定音频源
  python3 stream_pc_audio_pulse.py --robot-ip 10.42.0.75 --source alsa_output.pci-0000_00_1f.3.analog-stereo.monitor
        """
    )

    parser.add_argument(
        '--robot-ip',
        required=True,
        help='Reachy Mini 的 IP 地址'
    )
    parser.add_argument(
        '--list-sources',
        action='store_true',
        help='列出所有 PulseAudio 音频源'
    )
    parser.add_argument(
        '--source',
        metavar='SOURCE_NAME',
        help='指定 PulseAudio 源名称'
    )
    parser.add_argument(
        '--parec',
        action='store_true',
        help='使用 parec 而非 ffmpeg (更简单但功能较少)'
    )

    args = parser.parse_args()

    # 创建推流器
    streamer = PulseAudioStreamer(robot_ip=args.robot_ip)

    # 列出源
    if args.list_sources:
        streamer.list_pulseaudio_sources()
        return

    # 显示提示
    print("=" * 60)
    print("Linux 系统音频推流到 Reachy Mini")
    print("=" * 60)
    print(f"目标机器人: {args.robot_ip}")
    print(f"采样率: {StreamConfig.SAMPLE_RATE} Hz")
    print(f"声道: {StreamConfig.CHANNELS}")
    print("=" * 60)
    print()

    # 开始推流
    if args.parec:
        streamer.start_streaming_parec()
    else:
        streamer.start_streaming_ffmpeg(source_name=args.source)


if __name__ == "__main__":
    main()
