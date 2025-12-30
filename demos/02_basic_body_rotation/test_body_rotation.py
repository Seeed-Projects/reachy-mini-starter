#!/usr/bin/env python3
"""Reachy Mini 底座旋转演示

body_yaw: 控制身体/底座偏航角，范围 ±160 度
"""

import requests
import time


def rotate_base(count=3):
    """底座左右旋转

    Args:
        count: 旋转次数
    """
    base_url = "http://10.42.0.75:8000/api"

    print("=" * 50)
    print("Reachy Mini 底座旋转演示")
    print("=" * 50)

    # 启用电机
    print("\n启用电机...")
    requests.post(f"{base_url}/motors/set_mode/enabled")
    time.sleep(1)

    # 底座旋转
    print(f"\n🔄 底座旋转 {count} 次...")
    for i in range(count):
        print(f"  第 {i+1} 次: 左转 -> 右转")

        # 底座左转
        requests.post(f"{base_url}/move/goto", json={
            "body_yaw": 30,
            "duration": 1.0,
            "interpolation": "minjerk"
        })
        time.sleep(1.5)

        # 底座右转
        requests.post(f"{base_url}/move/goto", json={
            "body_yaw": -30,
            "duration": 1.0,
            "interpolation": "minjerk"
        })
        time.sleep(1.5)

    # 回正
    print("\n回到原位...")
    requests.post(f"{base_url}/move/goto", json={
        "body_yaw": 0,
        "duration": 1.0,
        "interpolation": "minjerk"
    })

    print("\n" + "=" * 50)
    print("完成!")
    print("=" * 50)


if __name__ == "__main__":
    rotate_base(3)
