#!/usr/bin/env python3
"""Reachy Mini 摇头晃脑动作演示

此 demo 使用 Reachy Mini SDK 在机器人本体上运行，展示多种头部动作：
- 顺时针/逆时针转动 (body_yaw): ±45°
- 前移动/后移动 (head x-axis): ±20mm (x轴: 正值向前, 负值向后)
- 向左移/向右移 (head y-axis): ±25mm (y轴: 正值向左, 负值向右)
- 向上移/向下移 (head z-axis): ±20mm (z轴: 正值向上, 负值向下)

每次动作都会先回到初始位置，再执行反向动作。

安全限制 (SDK 自动限制):
- Head Pitch/Roll: [-40°, +40°]
- Head Yaw: [-180°, +180°]
- Body Yaw: [-160°, +160°]
- Yaw Delta: Head 和 Body Yaw 最大差值 65°

运行平台: Reachy Mini 机器人本体
"""

import time
import numpy as np
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def look_around_action(count: int = 2):
    """摇头晃脑动作序列

    Args:
        count: 每个动作的重复次数
    """
    print("=" * 60)
    print("🤖 Reachy Mini 摇头晃脑演示")
    print("=" * 60)
    print(f"\n动作序列将重复 {count} 次:")
    print("  1️⃣  顺时针转动 -> 复位 -> 逆时针转动 -> 复位")
    print("  2️⃣  前移动 -> 复位 -> 后移动 -> 复位")
    print("  3️⃣  向左移 -> 复位 -> 向右移 -> 复位")
    print("  4️⃣  向上移 -> 复位 -> 向下移 -> 复位")
    print("=" * 60)

    # 使用 with 语句自动管理连接
    with ReachyMini() as mini:
        try:
            for cycle in range(count):
                print(f"\n{'='*60}")
                print(f"🔄 第 {cycle + 1}/{count} 轮动作")
                print('='*60)

                # ========== 动作 1: 顺时针/逆时针转动 ==========
                print("\n1️⃣  底座转动动作:")
                print("   顺时针转动 45° -> 复位 -> 逆时针转动 45° -> 复位")

                # 顺时针转动
                print("   ↻ 顺时针转动 45°...")
                mini.goto_target(
                    body_yaw=np.deg2rad(-45),
                    duration=0.4,
                    method="minjerk"
                )
                time.sleep(0.6)

                # 复位
                print("   ↺ 回到初始位置...")
                mini.goto_target(
                    body_yaw=0,
                    duration=0.4,
                    method="minjerk"
                )
                time.sleep(0.6)

                # 逆时针转动
                print("   ↺ 逆时针转动 45°...")
                mini.goto_target(
                    body_yaw=np.deg2rad(45),
                    duration=0.4,
                    method="minjerk"
                )
                time.sleep(0.6)

                # 复位
                print("   ↺ 回到初始位置...")
                mini.goto_target(
                    body_yaw=0,
                    duration=0.4,
                    method="minjerk"
                )
                time.sleep(0.6)

                # ========== 动作 2: 前移动/后移动 ==========
                print("\n2️⃣  前后移动动作:")
                print("   前移动 -> 复位 -> 后移动 -> 复位")

                # 前移动 (x 轴正值)
                print("   ⬆️  前移动 20mm...")
                mini.goto_target(
                    head=create_head_pose(x=20, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # 复位
                print("   ↺ 回到初始位置...")
                mini.goto_target(
                    head=create_head_pose(x=0, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # 后移动 (x 轴负值)
                print("   ⬇️  后移动 20mm...")
                mini.goto_target(
                    head=create_head_pose(x=-20, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # 复位
                print("   ↺ 回到初始位置...")
                mini.goto_target(
                    head=create_head_pose(x=0, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # ========== 动作 3: 向左移/向右移 ==========
                print("\n3️⃣  左右移动动作:")
                print("   向左移 -> 复位 -> 向右移 -> 复位")

                # 向左移 (y 轴正值)
                print("   ⬅️  向左移 25mm...")
                mini.goto_target(
                    head=create_head_pose(y=25, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # 复位
                print("   ↺ 回到初始位置...")
                mini.goto_target(
                    head=create_head_pose(y=0, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # 向右移 (y 轴负值)
                print("   ➡️  向右移 25mm...")
                mini.goto_target(
                    head=create_head_pose(y=-25, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # 复位
                print("   ↺ 回到初始位置...")
                mini.goto_target(
                    head=create_head_pose(y=0, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # ========== 动作 4: 向上移/向下移 ==========
                print("\n4️⃣  上下移动动作:")
                print("   向上移 -> 复位 -> 向下移 -> 复位")

                # 向上移 (z 轴正值)
                print("   ⬆️  向上移 20mm...")
                mini.goto_target(
                    head=create_head_pose(z=20, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # 复位
                print("   ↺ 回到初始位置...")
                mini.goto_target(
                    head=create_head_pose(z=0, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # 向下移 (z 轴负值)
                print("   ⬇️  向下移 20mm...")
                mini.goto_target(
                    head=create_head_pose(z=-20, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

                # 复位
                print("   ↺ 回到初始位置...")
                mini.goto_target(
                    head=create_head_pose(z=0, mm=True),
                    duration=0.25,
                    method="minjerk"
                )
                time.sleep(0.4)

            print(f"\n{'='*60}")
            print("🎉 所有动作完成!")
            print('='*60)

            # 回到初始位置
            print("\n🔄 回到初始位置...")
            mini.goto_target(
                body_yaw=0,
                head=create_head_pose(x=0, y=0, z=0, mm=True),
                duration=1.0,
                method="minjerk"
            )
            time.sleep(1.5)

        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断，正在停止...")
            # 回到初始位置
            mini.goto_target(
                body_yaw=0,
                head=create_head_pose(x=0, y=0, z=0, mm=True),
                duration=1.0,
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
    # 运行摇头晃脑动作，默认重复 2 次
    look_around_action(count=2)
