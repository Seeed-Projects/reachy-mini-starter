#!/usr/bin/env python3
"""Reachy Mini 音频控制脚本

通过 HTTP REST API 控制 Reachy Mini 机器人的音频功能。
"""

import requests
import json
import sys
from pathlib import Path
from typing import Optional

# 添加上级目录到路径以导入配置模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config

class ReachyMiniAudioClient:
    """Reachy Mini 音频控制客户端"""

    def __init__(self, robot_ip: str = None, port: int = None):
        # 如果未指定参数，从配置文件读取
        if robot_ip is None or port is None:
            config = get_config()
            robot_ip = config.robot_ip
            port = config.robot_port

        self.base_url = f"http://{robot_ip}:{port}/api"
        self._test_connection()

    def _test_connection(self):
        """测试连接"""
        try:
            resp = requests.get(f"{self.base_url}/volume/current", timeout=5)
            if resp.status_code == 200:
                print(f"✅ 成功连接到 Reachy Mini: {self.base_url}")
                return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
        return False

    # ===== 扬声器控制 =====

    def get_speaker_volume(self) -> int:
        """获取扬声器音量"""
        resp = requests.get(f"{self.base_url}/volume/current")
        data = resp.json()
        return data.get("volume", 0)

    def set_speaker_volume(self, volume: int) -> dict:
        """设置扬声器音量 (0-100)"""
        if not 0 <= volume <= 100:
            raise ValueError("音量必须在 0-100 之间")
        resp = requests.post(
            f"{self.base_url}/volume/set",
            json={"volume": volume}
        )
        return resp.json()

    def play_test_sound(self) -> dict:
        """播放测试音"""
        resp = requests.post(f"{self.base_url}/volume/test-sound")
        return resp.json()

    # ===== 麦克风控制 =====

    def get_microphone_volume(self) -> int:
        """获取麦克风增益"""
        resp = requests.get(f"{self.base_url}/volume/microphone/current")
        data = resp.json()
        return data.get("volume", 0)

    def set_microphone_volume(self, volume: int) -> dict:
        """设置麦克风增益 (0-100)"""
        if not 0 <= volume <= 100:
            raise ValueError("增益必须在 0-100 之间")
        resp = requests.post(
            f"{self.base_url}/volume/microphone/set",
            json={"volume": volume}
        )
        return resp.json()


def main():
    """主函数 - 演示音频控制功能"""
    print("=" * 50)
    print("Reachy Mini 音频控制")
    print("=" * 50)

    # 初始化客户端（从配置文件读取）
    client = ReachyMiniAudioClient()

    print("\n----- 扬声器控制 -----")

    # 获取当前音量
    current_vol = client.get_speaker_volume()
    print(f"当前扬声器音量: {current_vol}%")

    # 设置音量
    print("\n设置音量为 80%...")
    result = client.set_speaker_volume(50)
    print(f"设置结果: {result}")

    # 播放测试音
    print("\n🔊 播放测试音...")
    result = client.play_test_sound()
    print(f"播放结果: {result}")

    print("\n----- 麦克风控制 -----")

    # 获取麦克风增益
    mic_vol = client.get_microphone_volume()
    print(f"当前麦克风增益: {mic_vol}%")

    # 设置麦克风增益
    print("\n设置麦克风增益为 70%...")
    result = client.set_microphone_volume(70)
    print(f"设置结果: {result}")

    print("\n" + "=" * 50)
    print("完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
