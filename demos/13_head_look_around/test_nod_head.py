#!/usr/bin/env python3
"""Reachy Mini 头部点头演示

此 demo 使用 Reachy Mini SDK 在机器人本体上运行，研究头部上下点头：
- 头部向上看 (head pitch): -15°
- 头部向下看 (head pitch): +15°

不移动底盘，只转动头部来测试 head pitch 参数的效果。

参考 PC 版本的 REST API:
"head_pose": {"pitch": 15}  # 直接使用度数

安全限制 (SDK 自动限制):
- Head Pitch: [-40°, +40°]

运行平台: Reachy Mini 机器人本体
"""

import time
import numpy as np
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


def test_nod_head(count: int = 3):
    """测试头部上下点头

    Args:
        count: 点头次数
    """
    print("=" * 60)
    print("🤖 Reachy Mini 头部点头测试")
    print("=" * 60)
    print(f"\n测试头部上下点头 {count} 次:")
    print("  向上看 15° -> 向下看 15°")
    print("=" * 60)

    # 使用 with 语句自动管理连接
    with ReachyMini() as mini:
        try:
            for cycle in range(count):
                print(f"\n{'='*60}")
                print(f"🔄 第 {cycle + 1}/{count} 次点头")
                print('='*60)

                # 向上看 - pitch 负值
                print("\n   ⬆️  向上看 15° (pitch=-15)...")
                mini.goto_target(
                    head=create_head_pose(
                        pitch=-15  # 负值向上看
                    ),
                    duration=0.8,
                    method="minjerk"
                )
                time.sleep(1.0)

                # 向下看 - pitch 正值
                print("   ⬇️  向下看 15° (pitch=15)...")
                mini.goto_target(
                    head=create_head_pose(
                        pitch=15  # 正值向下看
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
    # 运行头部点头测试，默认重复 3 次
    test_nod_head(count=3)
