#!/usr/bin/env python3
"""Reachy Mini 摇头动作演示"""

import requests
import time


def shake_head(count=3):
    """摇头动作

    Args:
        count: 摇头次数
    """
    base_url = "http://10.42.0.75:8000/api"

    print("=" * 50)
    print("Reachy Mini 摇头演示")
    print("=" * 50)

    # 启用电机
    print("\n启用电机...")
    requests.post(f"{base_url}/motors/set_mode/enabled")
    time.sleep(1)

    # 摇头
    print(f"\n😓 摇头 {count} 次...")
    for i in range(count):
        print(f"  第 {i+1} 次: 左转 -> 右转")

        # 左转
        requests.post(f"{base_url}/move/goto", json={
            "head_pose": {"yaw": 20},
            "duration": 0.8,
            "interpolation": "minjerk"
        })
        time.sleep(1.0)

        # 右转
        requests.post(f"{base_url}/move/goto", json={
            "head_pose": {"yaw": -20},
            "duration": 0.8,
            "interpolation": "minjerk"
        })
        time.sleep(1.0)

    # 回正
    print("\n回到原位...")
    requests.post(f"{base_url}/move/goto", json={
        "head_pose": {"yaw": 0},
        "duration": 0.8,
        "interpolation": "minjerk"
    })

    print("\n" + "=" * 50)
    print("完成!")
    print("=" * 50)


if __name__ == "__main__":
    shake_head(3)
