#!/usr/bin/env python3
"""Reachy Mini 音频流服务 - 客户端测试脚本

这个脚本用于从局域网内的其他设备测试音频流 API。

用法:
    # 测试所有 API
    python3 test_client.py

    # 指定机器人 IP
    python3 test_client.py --robot-ip 10.42.0.75

    # 仅测试特定功能
    python3 test_client.py --test-only file
"""

import argparse
import json
import sys
import time
from typing import Optional

import requests


class AudioStreamClient:
    """音频流服务客户端."""

    def __init__(self, robot_ip: str = "127.0.0.1", port: int = 8001):
        """初始化客户端.

        Args:
            robot_ip: Reachy Mini 的 IP 地址
            port: API 服务端口
        """
        self.base_url = f"http://{robot_ip}:{port}"
        self.timeout = 10

    def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """发送 HTTP 请求.

        Args:
            method: HTTP 方法
            endpoint: API 端点
            data: 请求数据

        Returns:
            响应数据
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            print(f"❌ 连接失败: 无法连接到 {url}")
            print(f"   请检查:")
            print(f"   1. Reachy Mini 是否开机")
            print(f"   2. 服务是否已启动 (python3 audio_stream_server.py)")
            print(f"   3. IP 地址是否正确: {robot_ip}")
            sys.exit(1)
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时: {url}")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP 错误: {e.response.status_code}")
            print(f"   {e.response.text}")
            return e.response.json() if e.response.headers.get("content-type") == "application/json" else {}
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            sys.exit(1)

    def get_status(self) -> dict:
        """获取服务状态."""
        print("\n>>> 获取服务状态...")
        result = self._request("GET", "/stream/status")
        print(f"✅ 状态: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result

    def health_check(self) -> dict:
        """健康检查."""
        print("\n>>> 健康检查...")
        result = self._request("GET", "/health")
        print(f"✅ 健康: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result

    def start_stream(self, port: int = 5001, sample_rate: int = 48000, channels: int = 1) -> dict:
        """启动 UDP 音频流接收.

        Args:
            port: UDP 端口
            sample_rate: 采样率
            channels: 声道数
        """
        print(f"\n>>> 启动 UDP 音频流接收 (port={port}, sr={sample_rate}, ch={channels})...")
        data = {
            "port": port,
            "sample_rate": sample_rate,
            "channels": channels,
        }
        result = self._request("POST", "/stream/start", data)
        print(f"✅ 已启动: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result

    def stop_stream(self) -> dict:
        """停止 UDP 音频流接收."""
        print("\n>>> 停止 UDP 音频流接收...")
        result = self._request("POST", "/stream/stop")
        print(f"✅ 已停止: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result

    def play_file(self, file_path: str, sample_rate: Optional[int] = None) -> dict:
        """播放本地音频文件.

        Args:
            file_path: 音频文件路径 (在 Reachy Mini 上)
            sample_rate: 目标采样率
        """
        print(f"\n>>> 播放本地文件: {file_path}")
        data = {"file_path": file_path}
        if sample_rate:
            data["sample_rate"] = sample_rate
        result = self._request("POST", "/stream/play_file", data)
        print(f"✅ 开始播放: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result

    def play_url(self, url: str, sample_rate: Optional[int] = None) -> dict:
        """播放在线音频 URL.

        Args:
            url: 音频 URL
            sample_rate: 目标采样率
        """
        print(f"\n>>> 播放在线 URL: {url}")
        data = {"url": url}
        if sample_rate:
            data["sample_rate"] = sample_rate
        result = self._request("POST", "/stream/play_url", data)
        print(f"✅ 开始播放: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result


def run_tests(client: AudioStreamClient, test_only: Optional[str] = None):
    """运行测试.

    Args:
        client: 客户端实例
        test_only: 仅测试指定功能 (status/file/url/stream)
    """
    print("=" * 60)
    print("Reachy Mini 音频流服务 - 客户端测试")
    print("=" * 60)
    print(f"服务地址: {client.base_url}")

    # 健康检查
    if test_only is None or test_only == "status":
        client.health_check()
        client.get_status()

    # 文件播放测试
    if test_only is None or test_only == "file":
        print("\n" + "-" * 60)
        print("测试 1: 播放本地文件")
        print("-" * 60)

        # 请根据实际情况修改路径
        test_file = "/home/pollen/prompt_audio_1.wav"

        print(f"\n注意: 请确保文件存在于 Reachy Mini 上: {test_file}")
        print("按 Enter 继续测试文件播放，或跳过输入 's'...", end=" ")
        if input().strip().lower() != 's':
            client.play_file(test_file)
            client.play_file(test_file, sample_rate=16000)
            print("等待播放完成 (5秒)...")
            time.sleep(5)

    # URL 播放测试
    if test_only is None or test_only == "url":
        print("\n" + "-" * 60)
        print("测试 2: 播放在线 URL")
        print("-" * 60)

        print("\n注意: 需要 Reachy Mini 有网络连接")
        print("按 Enter 继续 URL 测试，或跳过输入 's'...", end=" ")
        if input().strip().lower() != 's':
            # 示例 URL，请替换为实际可用的音频 URL
            test_url = "https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg"
            client.play_url(test_url)
            print("等待播放完成 (10秒)...")
            time.sleep(10)

    # UDP 流测试
    if test_only is None or test_only == "stream":
        print("\n" + "-" * 60)
        print("测试 3: UDP 音频流接收")
        print("-" * 60)

        print("\n注意: UDP 流需要发送端配合")
        print("按 Enter 继续流测试，或跳过输入 's'...", end=" ")
        if input().strip().lower() != 's':
            # 启动流接收
            client.start_stream(port=5001, sample_rate=48000, channels=1)
            print("\n流接收已启动，等待 UDP 数据包...")
            print("按 Enter 停止流接收...", end=" ")
            input()
            client.stop_stream()

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


def print_curl_examples(robot_ip: str):
    """打印 curl 命令示例.

    Args:
        robot_ip: 机器人 IP 地址
    """
    print("\n" + "=" * 60)
    print("Curl 命令示例")
    print("=" * 60)

    print("\n1. 播放本地文件:")
    print(f"""curl -X POST http://{robot_ip}:8001/stream/play_file \\
  -H "Content-Type: application/json" \\
  -d '{{"file_path": "/home/pollen/prompt_audio_1.wav"}}'""")

    print("\n2. 播放本地文件 (指定采样率):")
    print(f"""curl -X POST http://{robot_ip}:8001/stream/play_file \\
  -H "Content-Type: application/json" \\
  -d '{{"file_path": "/home/pollen/prompt_audio_1.wav", "sample_rate": 16000}}'""")

    print("\n3. 查看服务状态:")
    print(f"""curl http://{robot_ip}:8001/stream/status""")

    print("\n4. 启动 UDP 流接收:")
    print(f"""curl -X POST http://{robot_ip}:8001/stream/start \\
  -H "Content-Type: application/json" \\
  -d '{{"port": 5001, "sample_rate": 48000, "channels": 1}}'""")

    print("\n5. 停止 UDP 流接收:")
    print(f"""curl -X POST http://{robot_ip}:8001/stream/stop""")

    print("\n6. 播放在线音频 URL:")
    print(f"""curl -X POST http://{robot_ip}:8001/stream/play_url \\
  -H "Content-Type: application/json" \\
  -d '{{"url": "https://example.com/audio.wav"}}'""")

    print("=" * 60)


def main():
    """主函数."""
    parser = argparse.ArgumentParser(description="Reachy Mini 音频流服务客户端测试")
    parser.add_argument(
        "--robot-ip",
        default="127.0.0.1",
        help="Reachy Mini 的 IP 地址 (默认: 127.0.0.1)",
    )
    parser.add_argument(
        "--test-only",
        choices=["status", "file", "url", "stream"],
        help="仅测试指定功能",
    )
    parser.add_argument(
        "--curl-examples",
        action="store_true",
        help="显示 curl 命令示例",
    )

    args = parser.parse_args()

    # 创建客户端
    client = AudioStreamClient(robot_ip=args.robot_ip)

    # 显示 curl 示例
    if args.curl_examples:
        print_curl_examples(args.robot_ip)
        return

    # 运行测试
    run_tests(client, test_only=args.test_only)


if __name__ == "__main__":
    main()
