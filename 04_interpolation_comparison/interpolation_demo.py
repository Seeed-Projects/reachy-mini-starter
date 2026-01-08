"""
Reachy Mini 插值方法机器人演示 (Demo 4b)

在真实机器人上对比不同插值方法的运动效果。
支持单个方法分析、并排对比、交互式调参等模式。

功能：
1. 单个插值方法演示和分析
2. 两种方法并排对比
3. 所有方法循环对比
4. 实时曲线显示
5. 交互式参数调整

前置条件：
    pip install reachy-mini numpy matplotlib

使用：
    # 使用 MIN_JERK 方法演示
    python interpolation_demo.py --method MIN_JERK

    # 对比两种方法
    python interpolation_demo.py --compare LINEAR MIN_JERK

    # 对比所有方法
    python interpolation_demo.py --compare-all

    # 交互式模式
    python interpolation_demo.py --interactive
"""

import argparse
import math
import sys
import time
from enum import Enum
from typing import List, Tuple, Optional

import numpy as np

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not installed.")

try:
    from reachy_mini import ReachyMini
    from reachy_mini.utils import create_head_pose
    from reachy_mini.utils.interpolation import InterpolationTechnique
    REACHY_AVAILABLE = True
except ImportError:
    REACHY_AVAILABLE = False
    print("Warning: reachy-mini not installed.")


class Method(Enum):
    """插值方法枚举"""
    LINEAR = "LINEAR"
    MIN_JERK = "MIN_JERK"
    EASE_IN_OUT = "EASE_IN_OUT"
    CARTOON = "CARTOON"

    def to_sdk_enum(self):
        """转换为 SDK 枚举"""
        mapping = {
            Method.LINEAR: InterpolationTechnique.LINEAR,
            Method.MIN_JERK: InterpolationTechnique.MIN_JERK,
            Method.EASE_IN_OUT: InterpolationTechnique.EASE_IN_OUT,
            Method.CARTOON: InterpolationTechnique.CARTOON,
        }
        return mapping[self]

    def description(self):
        """方法描述"""
        descriptions = {
            Method.LINEAR: "匀速运动，加速度突变",
            Method.MIN_JERK: "最平滑，加速度连续（推荐）",
            Method.EASE_IN_OUT: "S形曲线，两端慢中间快",
            Method.CARTOON: "夸张效果，两端很慢中间快"
        }
        return descriptions[self]


class MotionProfile:
    """运动轨迹记录器"""

    def __init__(self):
        self.times = []
        self.positions = []
        self.start_time = None

    def start(self):
        """开始记录"""
        self.start_time = time.time()
        self.times = []
        self.positions = []

    def add_point(self, position):
        """添加记录点"""
        if self.start_time is None:
            return

        elapsed = time.time() - self.start_time
        self.times.append(elapsed)
        self.positions.append(position)

    def get_trajectory(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取轨迹"""
        return np.array(self.times), np.array(self.positions)


class RobotInterpolator:
    """机器人插值演示器"""

    def __init__(self, reachy_mini):
        """初始化演示器"""
        self.mini = reachy_mini
        self.current_method = Method.MIN_JERK
        self.duration = 1.0
        self.pitch_amplitude = 20.0  # 度
        self.yaw_amplitude = 0.0

        # 记录轨迹
        self.profile = MotionProfile()

        print(f"机器人插值演示器初始化完成")
        print(f"默认方法: {self.current_method.value}")
        print(f"默认时长: {self.duration}s")

    def reset_position(self):
        """重置到中心位置"""
        try:
            center_pose = create_head_pose()
            self.mini.goto_target(
                head=center_pose,
                duration=0.5,
                method=InterpolationTechnique.MIN_JERK
            )
            time.sleep(0.6)
        except Exception as e:
            print(f"重置位置错误: {e}")

    def execute_motion(self, method: Method, record: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """执行运动

        Args:
            method: 插值方法
            record: 是否记录轨迹

        Returns:
            (times, positions) 轨迹数据
        """
        print(f"\n执行方法: {method.value}")
        print(f"描述: {method.description()}")
        print(f"时长: {self.duration}s")

        # 重置位置
        self.reset_position()

        # 计算目标姿态
        target_pose = create_head_pose(
            pitch=self.pitch_amplitude,
            yaw=self.yaw_amplitude,
            degrees=True
        )

        # 开始记录
        if record:
            self.profile.start()

        # 执行运动
        print("开始运动...")
        try:
            self.mini.goto_target(
                head=target_pose,
                duration=self.duration,
                method=method.to_sdk_enum()
            )
        except Exception as e:
            print(f"运动执行错误: {e}")
            return np.array([]), np.array([])

        # 等待运动完成
        time.sleep(self.duration + 0.1)

        # 返回到中心
        print("返回中心...")
        try:
            self.mini.goto_target(
                head=create_head_pose(),
                duration=self.duration,
                method=method.to_sdk_enum()
            )
        except Exception as e:
            print(f"返回中心错误: {e}")

        time.sleep(self.duration + 0.1)

        # 返回轨迹
        if record:
            return self.profile.get_trajectory()
        else:
            return np.array([]), np.array([])

    def compare_methods(self, method1: Method, method2: Method):
        """对比两种方法"""
        print("\n" + "=" * 60)
        print("插值方法对比")
        print("=" * 60)
        print(f"方法 1: {method1.value} - {method1.description()}")
        print(f"方法 2: {method2.value} - {method2.description()}")
        print()

        # 存储轨迹
        trajectories = {}

        # 执行方法 1
        print("\n【执行方法 1】")
        times1, positions1 = self.execute_motion(method1, record=True)
        trajectories[method1.value] = (times1, positions1)

        time.sleep(1)

        # 执行方法 2
        print("\n【执行方法 2】")
        times2, positions2 = self.execute_motion(method2, record=True)
        trajectories[method2.value] = (times2, positions2)

        # 显示对比
        if MATPLOTLIB_AVAILABLE and len(times1) > 0 and len(times2) > 0:
            self._plot_comparison(trajectories)

    def compare_all(self):
        """对比所有方法"""
        methods = list(Method)

        print("\n" + "=" * 60)
        print("对比所有插值方法")
        print("=" * 60)

        trajectories = {}

        for i, method in enumerate(methods):
            print(f"\n[{i+1}/{len(methods)}] {method.value}")

            times, positions = self.execute_motion(method, record=True)
            trajectories[method.value] = (times, positions)

            time.sleep(0.5)

        # 显示对比
        if MATPLOTLIB_AVAILABLE:
            self._plot_all_comparison(trajectories)

    def analyze_method(self, method: Method):
        """详细分析单个方法"""
        print("\n" + "=" * 60)
        print(f"详细分析: {method.value}")
        print("=" * 60)
        print(f"描述: {method.description()}")
        print()

        # 执行运动
        times, positions = self.execute_motion(method, record=True)

        if len(times) == 0:
            print("没有记录到轨迹数据")
            return

        # 分析统计
        print("\n轨迹分析:")
        print(f"  记录点数: {len(times)}")
        print(f"  实际时长: {times[-1]:.3f}s")
        print(f"  目标时长: {self.duration}s")
        print(f"  最大位置: {np.max(positions):.2f}")
        print(f"  最小位置: {np.min(positions):.2f}")

        # 计算速度和加速度
        if len(times) > 1:
            dt = np.diff(times)
            dp = np.diff(positions)
            velocities = dp / dt

            if len(velocities) > 1:
                dv = np.diff(velocities)
                accelerations = dv / dt[:-1]

                print(f"\n速度统计:")
                print(f"  最大速度: {np.max(np.abs(velocities)):.2f} deg/s")
                print(f"  平均速度: {np.mean(np.abs(velocities)):.2f} deg/s")

                print(f"\n加速度统计:")
                print(f"  最大加速度: {np.max(np.abs(accelerations)):.2f} deg/s²")
                print(f"  平均加速度: {np.mean(np.abs(accelerations)):.2f} deg/s²")

        # 绘制曲线
        if MATPLOTLIB_AVAILABLE:
            self._plot_single_method(times, positions, method)

    def _plot_comparison(self, trajectories: dict):
        """绘制对比图"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        methods = list(trajectories.keys())

        # 位置曲线
        ax = axes[0]
        for method_name in methods:
            times, positions = trajectories[method_name]
            if len(times) > 0:
                ax.plot(times, positions, label=method_name, linewidth=2, marker='o', markersize=3)

        ax.set_xlabel('时间 (秒)', fontsize=12)
        ax.set_ylabel('俯仰角 (度)', fontsize=12)
        ax.set_title('位置曲线对比', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 速度曲线
        ax = axes[1]
        for method_name in methods:
            times, positions = trajectories[method_name]
            if len(times) > 1:
                dt = np.diff(times)
                dp = np.diff(positions)
                velocities = dp / dt
                velocity_times = (times[:-1] + times[1:]) / 2
                ax.plot(velocity_times, velocities, label=method_name, linewidth=2)

        ax.set_xlabel('时间 (秒)', fontsize=12)
        ax.set_ylabel('速度 (度/秒)', fontsize=12)
        ax.set_title('速度曲线对比', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.suptitle(f'插值方法对比 (时长={self.duration}s, 幅度={self.pitch_amplitude}°)',
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.show()

    def _plot_all_comparison(self, trajectories: dict):
        """绘制所有方法对比"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        methods = list(trajectories.keys())
        colors = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#FFA07A']

        # 位置曲线
        ax = axes[0, 0]
        for i, method_name in enumerate(methods):
            times, positions = trajectories[method_name]
            if len(times) > 0:
                ax.plot(times, positions, label=method_name, linewidth=2, color=colors[i])
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('俯仰角 (度)')
        ax.set_title('位置曲线', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 速度曲线
        ax = axes[0, 1]
        for i, method_name in enumerate(methods):
            times, positions = trajectories[method_name]
            if len(times) > 1:
                dt = np.diff(times)
                dp = np.diff(positions)
                velocities = dp / dt
                velocity_times = (times[:-1] + times[1:]) / 2
                ax.plot(velocity_times, velocities, label=method_name, linewidth=2, color=colors[i])
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('速度 (度/秒)')
        ax.set_title('速度曲线', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 加速度曲线
        ax = axes[1, 0]
        for i, method_name in enumerate(methods):
            times, positions = trajectories[method_name]
            if len(times) > 2:
                dt = np.diff(times)
                dp = np.diff(positions)
                velocities = dp / dt
                dv = np.diff(velocities)
                accelerations = dv / dt[:-1]
                accel_times = (times[1:-1] + times[2:]) / 2
                ax.plot(accel_times, accelerations, label=method_name, linewidth=2, color=colors[i])
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('加速度 (度/秒²)')
        ax.set_title('加速度曲线', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 对比表
        ax = axes[1, 1]
        ax.axis('off')

        # 创建对比数据
        comparison_data = []
        for method_name in methods:
            times, positions = trajectories[method_name]
            if len(times) > 2:
                dt = np.diff(times)
                dp = np.diff(positions)
                velocities = dp / dt
                max_vel = np.max(np.abs(velocities))

                dv = np.diff(velocities)
                accelerations = dv / dt[:-1]
                max_accel = np.max(np.abs(accelerations))

                comparison_data.append([method_name, f'{max_vel:.1f}', f'{max_accel:.1f}'])

        # 绘制表格
        table = ax.table(
            cellText=comparison_data,
            colLabels=['方法', '最大速度', '最大加速度'],
            cellLoc='center',
            loc='center',
            bbox=[0, 0, 1, 1]
        )

        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2)

        # 设置表头
        for i in range(3):
            table[(0, i)].set_facecolor('#4ECDC4')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # 设置行
        for i in range(1, 5):
            for j in range(3):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')

        ax.set_title('统计对比', fontweight='bold', pad=20)

        plt.suptitle('所有插值方法对比', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.show()

    def _plot_single_method(self, times, positions, method: Method):
        """绘制单个方法的详细曲线"""
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # 位置
        axes[0].plot(times, positions, 'b-', linewidth=2)
        axes[0].set_xlabel('时间 (秒)')
        axes[0].set_ylabel('俯仰角 (度)')
        axes[0].set_title('位置')
        axes[0].grid(True, alpha=0.3)

        # 速度
        if len(times) > 1:
            dt = np.diff(times)
            dp = np.diff(positions)
            velocities = dp / dt
            velocity_times = (times[:-1] + times[1:]) / 2
            axes[1].plot(velocity_times, velocities, 'g-', linewidth=2)
        axes[1].set_xlabel('时间 (秒)')
        axes[1].set_ylabel('速度 (度/秒)')
        axes[1].set_title('速度')
        axes[1].grid(True, alpha=0.3)

        # 加速度
        if len(times) > 2:
            dv = np.diff(velocities)
            accelerations = dv / dt[:-1]
            accel_times = (times[1:-1] + times[2:]) / 2
            axes[2].plot(accel_times, accelerations, 'r-', linewidth=2)
        axes[2].set_xlabel('时间 (秒)')
        axes[2].set_ylabel('加速度 (度/秒²)')
        axes[2].set_title('加速度')
        axes[2].grid(True, alpha=0.3)

        plt.suptitle(f'{method.value} 方法详细分析', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()

    def set_parameters(self, duration=None, pitch=None, yaw=None):
        """设置参数"""
        if duration is not None:
            self.duration = duration
        if pitch is not None:
            self.pitch_amplitude = pitch
        if yaw is not None:
            self.yaw_amplitude = yaw


def interactive_mode(demo: RobotInterpolator):
    """交互式模式"""
    print("\n" + "=" * 60)
    print("交互式插值方法演示")
    print("=" * 60)
    print("\n命令:")
    print("  method <LINEAR|MIN_JERK|EASE_IN_OUT|CARTOON> - 设置方法")
    print("  duration <秒> - 设置运动时长")
    print("  pitch <度> - 设置俯仰角幅度")
    print("  yaw <度> - 设置偏航角幅度")
    print("  run - 执行当前方法")
    print("  compare <方法1> <方法2> - 对比两种方法")
    print("  all - 对比所有方法")
    print("  reset - 重置参数")
    print("  quit - 退出")
    print()

    while True:
        try:
            cmd = input(f"\n[{demo.current_method.value}] > ").strip().split()
            if not cmd:
                continue

            if cmd[0] == 'quit' or cmd[0] == 'q':
                break

            elif cmd[0] == 'method' and len(cmd) > 1:
                try:
                    method = Method[cmd[1].upper()]
                    demo.current_method = method
                    print(f"方法设置为: {method.value}")
                except KeyError:
                    print(f"未知方法: {cmd[1]}")

            elif cmd[0] == 'duration' and len(cmd) > 1:
                try:
                    duration = float(cmd[1])
                    demo.set_parameters(duration=duration)
                    print(f"时长设置为: {duration}s")
                except ValueError:
                    print("无效的时长")

            elif cmd[0] == 'pitch' and len(cmd) > 1:
                try:
                    pitch = float(cmd[1])
                    demo.set_parameters(pitch=pitch)
                    print(f"俯仰角设置为: {pitch}°")
                except ValueError:
                    print("无效的角度")

            elif cmd[0] == 'yaw' and len(cmd) > 1:
                try:
                    yaw = float(cmd[1])
                    demo.set_parameters(yaw=yaw)
                    print(f"偏航角设置为: {yaw}°")
                except ValueError:
                    print("无效的角度")

            elif cmd[0] == 'run':
                demo.execute_motion(demo.current_method, record=True)

            elif cmd[0] == 'compare' and len(cmd) > 2:
                try:
                    method1 = Method[cmd[1].upper()]
                    method2 = Method[cmd[2].upper()]
                    demo.compare_methods(method1, method2)
                except KeyError:
                    print("未知的方法")

            elif cmd[0] == 'all':
                demo.compare_all()

            elif cmd[0] == 'reset':
                demo.set_parameters(duration=1.0, pitch=20.0, yaw=0.0)
                demo.current_method = Method.MIN_JERK
                print("参数已重置")

            else:
                print("未知命令")

        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"错误: {e}")

    print("\n退出交互模式")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reachy Mini 插值方法机器人演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用 MIN_JERK 方法
  python interpolation_demo.py --method MIN_JERK

  # 详细分析
  python interpolation_demo.py --method MIN_JERK --analyze

  # 对比两种方法
  python interpolation_demo.py --compare LINEAR MIN_JERK

  # 对比所有方法
  python interpolation_demo.py --compare-all

  # 交互式模式
  python interpolation_demo.py --interactive
        """
    )

    parser.add_argument(
        '--method',
        type=str,
        choices=['LINEAR', 'MIN_JERK', 'EASE_IN_OUT', 'CARTOON'],
        default='MIN_JERK',
        help='插值方法'
    )
    parser.add_argument(
        '--compare',
        nargs=2,
        metavar=('M1', 'M2'),
        help='对比两种方法'
    )
    parser.add_argument(
        '--compare-all',
        action='store_true',
        help='对比所有方法'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='详细分析模式'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='交互式模式'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=1.0,
        help='运动时长（秒）'
    )
    parser.add_argument(
        '--pitch',
        type=float,
        default=20.0,
        help='俯仰角变化（度）'
    )
    parser.add_argument(
        '--yaw',
        type=float,
        default=0.0,
        help='偏航角变化（度）'
    )
    parser.add_argument(
        '--backend',
        type=str,
        default='default',
        help='媒体后端'
    )

    args = parser.parse_args()

    # 检查依赖
    if not REACHY_AVAILABLE:
        print("Error: reachy-mini 未安装")
        print("请安装: pip install reachy-mini")
        sys.exit(1)

    print("=" * 60)
    print("Reachy Mini 插值方法机器人演示")
    print("=" * 60)

    # 连接机器人
    print("\n正在连接到 Reachy Mini...")
    try:
        with ReachyMini(media_backend=args.backend) as reachy_mini:
            print("连接成功！")

            # 创建演示器
            demo = RobotInterpolator(reachy_mini)
            demo.set_parameters(
                duration=args.duration,
                pitch=args.pitch,
                yaw=args.yaw
            )

            # 执行对应模式
            if args.interactive:
                # 交互式模式
                interactive_mode(demo)

            elif args.compare:
                # 对比两种方法
                method1 = Method[args.compare[0]]
                method2 = Method[args.compare[1]]
                demo.compare_methods(method1, method2)

            elif args.compare_all:
                # 对比所有方法
                demo.compare_all()

            else:
                # 单个方法
                method = Method[args.method]
                if args.analyze:
                    demo.analyze_method(method)
                else:
                    demo.execute_motion(method, record=True)

            # 重置位置
            print("\n重置机器人位置...")
            demo.reset_position()

    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
