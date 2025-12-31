#!/usr/bin/env python3
"""Reachy Mini 点头动作演示

pitch: 控制头部俯仰，负值=低头，正值=抬头
"""

import requests
import time
import sys
from pathlib import Path

# 添加上级目录到路径以导入配置模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config


def nod_head(count=3):
    """点头动作

    Args:
        count: 点头次数
    """
    config = get_config()
    base_url = config.base_url

    print("=" * 50)
    print("Reachy Mini 点头演示")
    print("=" * 50)

    # 启用电机
    print("\n启用电机...")
    requests.post(f"{base_url}/motors_set_mode/enabled")
    time.sleep(1)

    # 点头
    print(f"\n🫡 点头 {count} 次...")
    for i in range(count):
        print(f"  第 {i+1} 次: 低头 -> 复位 -> 抬头 -> 复位")

        # 低头 (负值=低头)
        requests.post(f"{base_url}/move/goto", json={
            "head_pose": {"pitch": -6},
            "duration": 0.4,
            "interpolation": "minjerk"
        })
        time.sleep(0.5)

        # 复位
        requests.post(f"{base_url}/move/goto", json={
            "head_pose": {"pitch": 0},
            "duration": 0.4,
            "interpolation": "minjerk"
        })
        time.sleep(0.5)

        # 抬头 (正值=抬头)
        requests.post(f"{base_url}/move/goto", json={
            "head_pose": {"pitch": 6},
            "duration": 0.4,
            "interpolation": "minjerk"
        })
        time.sleep(0.5)

        # 复位
        requests.post(f"{base_url}/move/goto", json={
            "head_pose": {"pitch": 0},
            "duration": 0.4,
            "interpolation": "minjerk"
        })
        time.sleep(0.5)

    # 回正
    print("\n回到原位...")
    requests.post(f"{base_url}/move/goto", json={
        "head_pose": {"pitch": 0},
        "duration": 0.8,
        "interpolation": "minjerk"
    })

    print("\n" + "=" * 50)
    print("完成!")
    print("=" * 50)


if __name__ == "__main__":
    nod_head(3)
