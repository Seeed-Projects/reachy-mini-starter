#!/usr/bin/env python3
"""Reachy Mini 头部画圈演示

此 demo 使用 Reachy Mini SDK 在机器人本体上运行，让头部连续转圈：
- 正转一圈：左 -> 上 -> 右 -> 下 -> 回中
- 反转一圈：右 -> 上 -> 左 -> 下 -> 回中

头部沿着圆形路径连续转动，而不是分段动作。

参考 PC 版本的 REST API:
"head_pose": {"yaw": x, "pitch": y}  # 同时控制 yaw 和 pitch

安全限制 (SDK 自动限制):
- Head Pitch: [-40°, +40°]
- Head Yaw: [-180°, +180°]

运行平台: Reachy Mini 机器人本体
"""

import time
import math
import numpy as np
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def head_circle_clockwise(mini, steps=12):
    """头部顺时针转一圈（左->上->右->下）

    Args:
        mini: ReachyMini 实例
        steps: 每圈的分步数，越多越平滑
    """
    print("\n   🔄 顺时针转一圈 (左->上->右->下)...")
    radius_yaw = 20   # 左右幅度
    radius_pitch = 15 # 上下幅度

    for i in range(steps + 1):
        angle = 2 * math.pi * i / steps  # 0 到 2π
        yaw = radius_yaw * math.cos(angle)      # cos: 1 -> 0 -> -1 -> 0 -> 1
        pitch = -radius_pitch * math.sin(angle) # -sin: 0 -> -1 -> 0 -> 1 -> 0

        mini.goto_target(
            head=create_head_pose(
                yaw=yaw,
                pitch=pitch
            ),
            duration=0.15,
            method="minjerk"
        )
        time.sleep(0.18)


def head_circle_counterclockwise(mini, steps=12):
    """头部逆时针转一圈（右->上->左->下）

    Args:
        mini: ReachyMini 实例
        steps: 每圈的分步数，越多越平滑
    """
    print("\n   🔄 逆时针转一圈 (右->上->左->下)...")
    radius_yaw = 20   # 左右幅度
    radius_pitch = 15 # 上下幅度

    for i in range(steps + 1):
        angle = 2 * math.pi * i / steps  # 0 到 2π
        yaw = -radius_yaw * math.cos(angle)      # -cos: -1 -> 0 -> 1 -> 0 -> -1
        pitch = -radius_pitch * math.sin(angle)  # -sin: 0 -> -1 -> 0 -> 1 -> 0

        mini.goto_target(
            head=create_head_pose(
                yaw=yaw,
                pitch=pitch
            ),
            duration=0.15,
            method="minjerk"
        )
        time.sleep(0.18)


def test_head_circle(count: int = 2):
    """测试头部画圈

    Args:
        count: 转圈次数（每圈包含一次顺时针和一次逆时针）
    """
    print("=" * 60)
    print("🤖 Reachy Mini 头部画圈测试")
    print("=" * 60)
    print(f"\n测试头部画圈 {count} 次:")
    print("  顺时针转一圈 -> 逆时针转一圈")
    print("=" * 60)

    # 使用 with 语句自动管理连接
    with ReachyMini() as mini:
        try:
            for cycle in range(count):
                print(f"\n{'='*60}")
                print(f"🔄 第 {cycle + 1}/{count} 轮画圈")
                print('='*60)

                # 顺时针转一圈
                head_circle_clockwise(mini, steps=12)
                time.sleep(0.5)

                # 回到正中
                print("\n   ↺ 回到正中...")
                mini.goto_target(
                    head=create_head_pose(
                        yaw=0,
                        pitch=0
                    ),
                    duration=0.5,
                    method="minjerk"
                )
                time.sleep(0.8)

                # 逆时针转一圈
                head_circle_counterclockwise(mini, steps=12)
                time.sleep(0.5)

                # 回到正中
                print("\n   ↺ 回到正中...")
                mini.goto_target(
                    head=create_head_pose(
                        yaw=0,
                        pitch=0
                    ),
                    duration=0.5,
                    method="minjerk"
                )
                time.sleep(0.8)

            print(f"\n{'='*60}")
            print("🎉 测试完成!")
            print('='*60)

        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断，正在停止...")
            # 回到正中
            mini.goto_target(
                head=create_head_pose(
                    yaw=0,
                    pitch=0
                ),
                duration=0.5,
                method="minjerk"
            )

        except Exception as e:
            print(f"\n\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("演示结束!")
    print("="*60)


if __name__ == "__main__":
    # 运行头部画圈测试，默认重复 2 次
    test_head_circle(count=2)
