#!/usr/bin/env python3
"""PC 音频实时推流到 Reachy Mini

这个脚本捕获电脑的音频输出，并实时推流到 Reachy Mini 播放。
实现远程音响功能。

运行方式:
    # 先在 Reachy Mini 上启动服务
    python3 audio_stream_server.py

    # 然后在 PC 上启动推流
    python3 stream_pc_audio.py --robot-ip 10.42.0.75

    # 指定音频输入设备
    python3 stream_pc_audio.py --robot-ip 10.42.0.75 --device "Stereo Mix"

依赖:
    pip install pyaudio numpy requests

功能:
    - 自动列出可用音频设备
    - 实时捕获电脑音频
    - OPUS 编码推流
    - 低延迟传输
"""

import argparse
import io
import logging
import sys
import time
import wave
import struct
import requests
from typing import Optional, List

try:
    import pyaudio
except ImportError:
    print("错误: 需要安装 pyaudio")
    print("安装方式:")
    print("  pip install pyaudio")
    print("  # 或在 Ubuntu 上:")
    print("  sudo apt-get install python3-pyaudio")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("错误: 需要安装 numpy")
    print("安装方式: pip install numpy")
    sys.exit(1)


# 配置
class StreamConfig:
    """推流配置."""

    # 音频参数
    SAMPLE_RATE = 48000
    CHANNELS = 1
    CHUNK_SIZE = 960  # 20ms @ 48kHz
    BIT_DEPTH = 16
    FORMAT = pyaudio.paInt16

    # OPUS 编码参数
    OPUS_FRAME_SIZE = 960  # 20ms @ 48kHz
    OPUS_BITRATE = 64000

    # 网络参数
    UDP_PORT = 5001

    # API 参数
    API_PORT = 8001


class AudioStreamer:
    """音频推流器."""

    def __init__(self, robot_ip: str, device_index: Optional[int] = None):
        """初始化推流器.

        Args:
            robot_ip: Reachy Mini 的 IP 地址
            device_index: 音频输入设备索引 (None = 默认设备)
        """
        self._logger = logging.getLogger(__name__)
        self._robot_ip = robot_ip
        self._device_index = device_index
        self._api_url = f"http://{robot_ip}:{StreamConfig.API_PORT}"
        self._is_streaming = False

        # 初始化 PyAudio
        self._pyaudio = pyaudio.PyAudio()

    def list_devices(self) -> None:
        """列出所有可用的音频输入设备."""
        print("\n可用的音频输入设备:")
        print("=" * 60)

        input_devices = []
        for i in range(self._pyaudio.get_device_count()):
            info = self._pyaudio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append((i, info))
                print(f"  [{i}] {info['name']}")
                print(f"      采样率: {int(info['defaultSampleRate'])} Hz")
                print(f"      声道数: {info['maxInputChannels']}")
                print()

        print("=" * 60)
        print("推荐设备 (虚拟音频输出):")
        print("  - Windows: 'Stereo Mix', 'Wave Out Mix', 'What U Hear'")
        print("  - macOS: 使用 Soundflower 或 BlackHole")
        print("  - Linux: 使用 PulseAudio 的 monitor device")
        print()

        return input_devices

    def _find_loopback_device(self) -> Optional[int]:
        """查找回环设备 (虚拟音频输出).

        Returns:
            设备索引，如果找不到则返回 None
        """
        loopback_keywords = [
            'stereo mix', 'wave out mix', 'what u hear',
            'loopback', 'monitor', 'soundflower', 'blackhole'
        ]

        for i in range(self._pyaudio.get_device_count()):
            info = self._pyaudio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                name_lower = info['name'].lower()
                for keyword in loopback_keywords:
                    if keyword in name_lower:
                        return i

        return None

    def _start_stream_receiver(self) -> bool:
        """启动 Reachy Mini 上的 PCM 流接收服务.

        Returns:
            是否成功启动
        """
        self._logger.info(f"正在启动 {self._robot_ip} 上的 PCM 流接收服务...")

        try:
            # 先停止已有的流
            try:
                response = requests.post(f"{self._api_url}/stream/stop", timeout=5)
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

    def _create_opus_stream(self) -> 'pyaudio.Stream':
        """创建音频输入流.

        Returns:
            PyAudio 流对象
        """
        device_index = self._device_index
        if device_index is None:
            # 尝试自动查找回环设备
            device_index = self._find_loopback_device()
            if device_index is not None:
                self._logger.info(f"自动检测到回环设备: [{device_index}]")
            else:
                self._logger.warning("未找到回环设备，使用默认输入设备")
                self._logger.warning("你将需要使用麦克风捕获电脑音频")

        try:
            stream = self._pyaudio.open(
                format=StreamConfig.FORMAT,
                channels=StreamConfig.CHANNELS,
                rate=StreamConfig.SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=StreamConfig.CHUNK_SIZE,
            )
            return stream
        except Exception as e:
            self._logger.error(f"创建音频流失败: {e}")
            self._logger.error("尝试使用其他音频设备")
            raise

    def start_streaming(self) -> None:
        """开始音频推流."""
        # 启动流接收服务
        if not self._start_stream_receiver():
            return

        # 创建音频流
        try:
            stream = self._create_opus_stream()
        except Exception:
            self._stop_stream_receiver()
            return

        self._is_streaming = True
        self._logger.info("开始音频推流...")
        self._logger.info("按 Ctrl+C 停止")

        try:
            # 使用 UDP socket 发送音频数据
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            packet_count = 0
            start_time = time.time()

            while self._is_streaming:
                try:
                    # 读取音频数据
                    data = stream.read(StreamConfig.CHUNK_SIZE, exception_on_overflow=False)

                    # 发送 UDP 数据包
                    sock.sendto(data, (self._robot_ip, StreamConfig.UDP_PORT))

                    packet_count += 1
                    if packet_count % 100 == 0:
                        elapsed = time.time() - start_time
                        rate = packet_count / elapsed
                        self._logger.debug(f"推流中... {rate:.1f} packet/s")

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self._logger.error(f"推流错误: {e}")
                    break

            sock.close()

        except Exception as e:
            self._logger.error(f"推流失败: {e}")
        finally:
            stream.close()
            self._stop_stream_receiver()
            self._logger.info("推流已停止")

    def stop_streaming(self) -> None:
        """停止音频推流."""
        self._is_streaming = False

    def __del__(self):
        """清理资源."""
        if hasattr(self, '_pyaudio'):
            self._pyaudio.terminate()


def main():
    """主函数."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
    )

    parser = argparse.ArgumentParser(
        description="将 PC 音频实时推流到 Reachy Mini 播放 (远程音响)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设备推流
  python3 stream_pc_audio.py --robot-ip 10.42.0.75

  # 列出可用设备
  python3 stream_pc_audio.py --list-devices

  # 指定音频设备
  python3 stream_pc_audio.py --robot-ip 10.42.0.75 --device 3

  # 自动检测回环设备
  python3 stream_pc_audio.py --robot-ip 10.42.0.75 --auto-loopback
        """
    )

    parser.add_argument(
        '--robot-ip',
        required=True,
        help='Reachy Mini 的 IP 地址'
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='列出所有可用的音频输入设备'
    )
    parser.add_argument(
        '--device',
        type=int,
        metavar='INDEX',
        help='指定音频输入设备索引'
    )
    parser.add_argument(
        '--auto-loopback',
        action='store_true',
        help='自动检测并使用回环设备'
    )

    args = parser.parse_args()

    # 创建推流器
    streamer = AudioStreamer(robot_ip=args.robot_ip)

    # 列出设备
    if args.list_devices:
        streamer.list_devices()
        return

    # 自动检测回环设备
    if args.auto_loopback:
        device_index = streamer._find_loopback_device()
        if device_index is not None:
            print(f"✅ 检测到回环设备: [{device_index}]")
            streamer._device_index = device_index
        else:
            print("⚠️  未检测到回环设备")
            print("\n请使用 --list-devices 查看可用设备")
            print("然后使用 --device INDEX 指定设备")
            return

    # 显示提示
    print("=" * 60)
    print("PC 音频实时推流到 Reachy Mini")
    print("=" * 60)
    print(f"目标机器人: {args.robot_ip}")
    print(f"采样率: {StreamConfig.SAMPLE_RATE} Hz")
    print(f"声道: {StreamConfig.CHANNELS}")
    print("=" * 60)
    print()
    print("提示:")
    print("  - 首次使用建议先运行 --list-devices 查看可用设备")
    print("  - 推荐使用虚拟音频输出设备 (如 Stereo Mix)")
    print("  - 按 Ctrl+C 停止推流")
    print()
    print("正在连接...")

    # 开始推流
    try:
        streamer.start_streaming()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        streamer.stop_streaming()


if __name__ == "__main__":
    main()
