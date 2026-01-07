#!/usr/bin/env python3
"""Reachy Mini 头部转动演示

此 demo 使用 Reachy Mini SDK 在机器人本体上运行，展示头部转动动作：
- 左右转头 (head yaw): ±20°
- 上下点头 (head pitch): ±15°

不移动底盘，只转动头部来测试 head yaw 和 pitch 参数的效果。

参考 PC 版本的 REST API:
"head_pose": {"yaw": 20, "pitch": 15}  # 直接使用度数

安全限制 (SDK 自动限制):
- Head Pitch: [-40°, +40°]
- Head Yaw: [-180°, +180°]

运行平台: Reachy Mini 机器人本体
"""

import time
import numpy as np
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def test_look_around(count: int = 3):
    """测试头部转动（左右+上下）

    Args:
        count: 转动次数
    """
    print("=" * 60)
    print("🤖 Reachy Mini 头部转动测试")
    print("=" * 60)
    print(f"\n测试头部转动 {count} 次:")
    print("  左转头 -> 右转头 -> 向上看 -> 向下看")
    print("=" * 60)

    # 使用 with 语句自动管理连接
    with ReachyMini() as mini:
        try:
            for cycle in range(count):
                print(f"\n{'='*60}")
                print(f"🔄 第 {cycle + 1}/{count} 次转动")
                print('='*60)

                # 向左转
                print("\n   ⬅️  向左转 20° (yaw=20)...")
                mini.goto_target(
                    head=create_head_pose(
                        yaw=20
                    ),
                    duration=0.8,
                    method="minjerk"
                )
                time.sleep(1.0)

                # 向右转
                print("   ➡️  向右转 20° (yaw=-20)...")
                mini.goto_target(
                    head=create_head_pose(
                        yaw=-20
                    ),
                    duration=0.8,
                    method="minjerk"
                )
                time.sleep(1.0)

                # 向上看
                print("   ⬆️  向上看 15° (pitch=-15)...")
                mini.goto_target(
                    head=create_head_pose(
                        pitch=-15
                    ),
                    duration=0.8,
                    method="minjerk"
                )
                time.sleep(1.0)

                # 向下看
                print("   ⬇️  向下看 15° (pitch=15)...")
                mini.goto_target(
                    head=create_head_pose(
                        pitch=15
                    ),
                    duration=0.8,
                    method="minjerk"
                )
                time.sleep(1.0)

            # 回正
            print(f"\n{'='*60}")
            print("🔄 回到正中...")
            print('='*60)
            mini.goto_target(
                head=create_head_pose(
                    yaw=0,
                    pitch=0
                ),
                duration=0.8,
                method="minjerk"
            )
            time.sleep(1.0)

            print(f"\n{'='*60}")
            print("🎉 测试完成!")
            print('='*60)

        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断，正在停止...")

        except Exception as e:
            print(f"\n\n❌ 发生错误: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("演示结束!")
    print("="*60)


if __name__ == "__main__":
    # 运行头部转动测试，默认重复 3 次
    test_look_around(count=3)
