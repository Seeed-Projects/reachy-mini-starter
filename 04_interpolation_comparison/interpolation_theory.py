"""
Reachy Mini 插值方法理论可视化 (Demo 4a)

无需机器人，通过 matplotlib 可视化对比四种插值方法的运动特性。
展示位置、速度、加速度、加加速度曲线的差异。

功能：
1. 四种插值方法曲线对比
2. 数学公式说明
3. 运动特性分析
4. 可导出图像

前置条件：
    pip install numpy matplotlib

使用：
    # 显示所有对比
    python interpolation_theory.py

    # 仅显示位置曲线
    python interpolation_theory.py --position-only

    # 导出图像
    python interpolation_theory.py --save interpolation_curves.png
"""

import argparse
import math
import sys
from dataclasses import dataclass
from enum import Enum

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False


class InterpolationMethod(Enum):
    """插值方法枚举"""
    LINEAR = "linear"
    MIN_JERK = "min_jerk"
    EASE_IN_OUT = "ease_in_out"
    CARTOON = "cartoon"

    def display_name(self):
        """显示名称"""
        names = {
            InterpolationMethod.LINEAR: "LINEAR (线性)",
            InterpolationMethod.MIN_JERK: "MIN_JERK (最小加加速度)",
            InterpolationMethod.EASE_IN_OUT: "EASE_IN_OUT (缓入缓出)",
            InterpolationMethod.CARTOON: "CARTOON (卡通)"
        }
        return names[self]

    def color(self):
        """颜色"""
        colors = {
            InterpolationMethod.LINEAR: '#FF6B6B',      # 红色
            InterpolationMethod.MIN_JERK: '#4ECDC4',    # 青色
            InterpolationMethod.EASE_IN_OUT: '#95E1D3', # 绿色
            InterpolationMethod.CARTOON: '#FFA07A'      # 橙色
        }
        return colors[self]

    def description(self):
        """方法描述"""
        descriptions = {
            InterpolationMethod.LINEAR: "匀速运动，加速度在起点/终点突变",
            InterpolationMethod.MIN_JERK: "最平滑，加速度连续，加加速度最小（推荐）",
            InterpolationMethod.EASE_IN_OUT: "柔和的S形曲线，两端慢中间快",
            InterpolationMethod.CARTOON: "夸张效果，两端很慢中间很快"
        }
        return descriptions[self]


@dataclass
class TrajectoryPoint:
    """轨迹点"""
    position: float
    velocity: float
    acceleration: float
    jerk: float


class InterpolationFunctions:
    """插值函数集合"""

    @staticmethod
    def linear(tau):
        """线性插值

        p(τ) = τ

        一阶导数（速度）: v(τ) = 1
        二阶导数（加速度）: a(τ) = 0
        三阶导数（加加速度）: j(τ) = 0
        """
        pos = tau
        vel = 1.0
        acc = 0.0
        jerk = 0.0
        return TrajectoryPoint(pos, vel, acc, jerk)

    @staticmethod
    def minimum_jerk(tau):
        """最小加加速度插值（7次多项式）

        p(τ) = 10τ³ - 15τ⁴ + 6τ⁵

        一阶导数（速度）: v(τ) = 30τ² - 60τ³ + 30τ⁴
        二阶导数（加速度）: a(τ) = 60τ - 180τ² + 120τ³
        三阶导数（加加速度）: j(τ) = 60 - 360τ + 360τ²
        """
        tau2 = tau * tau
        tau3 = tau2 * tau
        tau4 = tau3 * tau
        tau5 = tau4 * tau

        pos = 10 * tau3 - 15 * tau4 + 6 * tau5
        vel = 30 * tau2 - 60 * tau3 + 30 * tau4
        acc = 60 * tau - 180 * tau2 + 120 * tau3
        jerk = 60 - 360 * tau + 360 * tau2

        return TrajectoryPoint(pos, vel, acc, jerk)

    @staticmethod
    def ease_in_out(tau):
        """缓入缓出插值（3次多项式，S形曲线）

        p(τ) = 3τ² - 2τ³

        一阶导数（速度）: v(τ) = 6τ - 6τ²
        二阶导数（加速度）: a(τ) = 6 - 12τ
        三阶导数（加加速度）: j(τ) = -12
        """
        tau2 = tau * tau
        tau3 = tau2 * tau

        pos = 3 * tau2 - 2 * tau3
        vel = 6 * tau - 6 * tau2
        acc = 6 - 12 * tau
        jerk = -12.0

        return TrajectoryPoint(pos, vel, acc, jerk)

    @staticmethod
    def cartoon(tau):
        """卡通效果插值（5次多项式）

        p(τ) = 6τ⁵ - 15τ⁴ + 10τ³

        一阶导数（速度）: v(τ) = 30τ⁴ - 60τ³ + 30τ²
        二阶导数（加速度）: a(τ) = 120τ³ - 180τ² + 60τ
        三阶导数（加加速度）: j(τ) = 360τ² - 360τ + 60
        """
        tau2 = tau * tau
        tau3 = tau2 * tau
        tau4 = tau3 * tau
        tau5 = tau4 * tau

        pos = 6 * tau5 - 15 * tau4 + 10 * tau3
        vel = 30 * tau4 - 60 * tau3 + 30 * tau2
        acc = 120 * tau3 - 180 * tau2 + 60 * tau
        jerk = 360 * tau2 - 360 * tau + 60

        return TrajectoryPoint(pos, vel, acc, jerk)

    @classmethod
    def compute_trajectory(cls, method, num_points=100):
        """计算完整轨迹

        Args:
            method: 插值方法
            num_points: 采样点数

        Returns:
            (times, positions, velocities, accelerations, jerks)
        """
        times = np.linspace(0, 1, num_points)
        positions = []
        velocities = []
        accelerations = []
        jerks = []

        func_map = {
            InterpolationMethod.LINEAR: cls.linear,
            InterpolationMethod.MIN_JERK: cls.minimum_jerk,
            InterpolationMethod.EASE_IN_OUT: cls.ease_in_out,
            InterpolationMethod.CARTOON: cls.cartoon,
        }

        func = func_map[method]

        for t in times:
            point = func(t)
            positions.append(point.position)
            velocities.append(point.velocity)
            accelerations.append(point.acceleration)
            jerks.append(point.jerk)

        return times, positions, velocities, accelerations, jerks


class InterpolationVisualizer:
    """插值方法可视化器"""

    def __init__(self, figsize=(16, 10)):
        """初始化可视化器"""
        self.figsize = figsize
        self.methods = list(InterpolationMethod)

    def plot_comparison(self, position_only=False, save_path=None):
        """绘制对比图

        Args:
            position_only: 仅绘制位置曲线
            save_path: 保存路径（None 则不保存）
        """
        if position_only:
            self._plot_position_only(save_path)
        else:
            self._plot_full_comparison(save_path)

    def _plot_position_only(self, save_path):
        """仅绘制位置曲线"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))

        for method in self.methods:
            times, positions, _, _, _ = InterpolationFunctions.compute_trajectory(method)

            ax.plot(times, positions,
                   label=method.display_name(),
                   color=method.color(),
                   linewidth=2.5,
                   marker='o' if method == InterpolationMethod.LINEAR else '',
                   markevery=10,
                   markersize=4)

        ax.set_xlabel('归一化时间 τ = t/T', fontsize=14, fontweight='bold')
        ax.set_ylabel('归一化位置 p(τ)', fontsize=14, fontweight='bold')
        ax.set_title('插值方法位置曲线对比', fontsize=16, fontweight='bold')
        ax.legend(loc='lower right', fontsize=12)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.05)

        # 添加说明文字
        description = "\n".join([
            "● LINEAR: 直线路径，匀速运动",
            "● MIN_JERK: 平滑过渡，最自然的运动（推荐）",
            "● EASE_IN_OUT: S形曲线，两端慢中间快",
            "● CARTOON: 夸张的S形，效果更明显"
        ])
        ax.text(0.02, 0.98, description,
               transform=ax.transAxes,
               fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图像已保存到: {save_path}")

        plt.show()

    def _plot_full_comparison(self, save_path):
        """绘制完整对比图（位置、速度、加速度、加加速度）"""
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        fig.suptitle('插值方法运动特性对比', fontsize=18, fontweight='bold')

        # 位置
        ax = axes[0, 0]
        for method in self.methods:
            times, positions, _, _, _ = InterpolationFunctions.compute_trajectory(method)
            ax.plot(times, positions,
                   label=method.display_name(),
                   color=method.color(),
                   linewidth=2)
        ax.set_ylabel('位置', fontsize=12, fontweight='bold')
        ax.set_title('位置曲线', fontsize=14, fontweight='bold')
        ax.legend(loc='lower right', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.05)

        # 速度
        ax = axes[0, 1]
        for method in self.methods:
            times, _, velocities, _, _ = InterpolationFunctions.compute_trajectory(method)
            ax.plot(times, velocities,
                   label=method.display_name(),
                   color=method.color(),
                   linewidth=2)
        ax.set_ylabel('速度', fontsize=12, fontweight='bold')
        ax.set_title('速度曲线', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)

        # 加速度
        ax = axes[1, 0]
        for method in self.methods:
            times, _, _, accelerations, _ = InterpolationFunctions.compute_trajectory(method)
            ax.plot(times, accelerations,
                   label=method.display_name(),
                   color=method.color(),
                   linewidth=2)
        ax.set_xlabel('归一化时间 τ', fontsize=12, fontweight='bold')
        ax.set_ylabel('加速度', fontsize=12, fontweight='bold')
        ax.set_title('加速度曲线', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)

        # 加加速度
        ax = axes[1, 1]
        for method in self.methods:
            times, _, _, _, jerks = InterpolationFunctions.compute_trajectory(method)
            ax.plot(times, jerks,
                   label=method.display_name(),
                   color=method.color(),
                   linewidth=2)
        ax.set_xlabel('归一化时间 τ', fontsize=12, fontweight='bold')
        ax.set_ylabel('加加速度 (Jerk)', fontsize=12, fontweight='bold')
        ax.set_title('加加速度曲线', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 1)

        # 添加特性对比表
        self._add_comparison_table(fig)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图像已保存到: {save_path}")

        plt.show()

    def _add_comparison_table(self, fig):
        """添加特性对比表"""
        # 创建表格数据
        methods_short = ['LINEAR', 'MIN_JERK', 'EASE_IN_OUT', 'CARTOON']

        smoothness = ['⭐', '⭐⭐⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐']
        velocity_continuous = ['❌', '✅', '✅', '✅']
        acceleration_continuous = ['❌', '✅', '✅', '✅']
        min_jerk = ['❌', '✅', '❌', '❌']
        recommended = ['测试', '⭐推荐', '表情', '特效']

        cell_text = list(zip(smoothness, velocity_continuous, acceleration_continuous,
                            min_jerk, recommended))

        # 添加表格
        axes = fig.add_axes([0.12, -0.08, 0.8, 0.1])
        axes.axis('off')

        table = axes.table(
            cellText=cell_text,
            rowLabels=methods_short,
            colLabels=['平滑度', '速度连续', '加速度连续', '最小Jerk', '推荐场景'],
            cellLoc='center',
            loc='center',
            bbox=[0, 0, 1, 1]
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)

        # 设置表头样式
        for i in range(5):
            table[(0, i)].set_facecolor('#4ECDC4')
            table[(0, i)].set_text_props(weight='bold', color='white')

        # 设置行样式
        for i in range(1, 5):
            for j in range(5):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')


def print_theory():
    """打印理论说明"""
    print("=" * 70)
    print("插值方法理论说明")
    print("=" * 70)
    print()

    for method in InterpolationMethod:
        print(f"【{method.display_name()}】")
        print(f"  {method.description()}")
        print()

        if method == InterpolationMethod.LINEAR:
            print("  数学公式:")
            print("    位置: p(τ) = τ")
            print("    速度: v(τ) = 1")
            print("    加速度: a(τ) = 0")
            print()

        elif method == InterpolationMethod.MIN_JERK:
            print("  数学公式:")
            print("    位置: p(τ) = 10τ³ - 15τ⁴ + 6τ⁵")
            print("    速度: v(τ) = 30τ² - 60τ³ + 30τ⁴")
            print("    加速度: a(τ) = 60τ - 180τ² + 120τ³")
            print("    加加速度: j(τ) = 60 - 360τ + 360τ²")
            print()

        elif method == InterpolationMethod.EASE_IN_OUT:
            print("  数学公式:")
            print("    位置: p(τ) = 3τ² - 2τ³")
            print("    速度: v(τ) = 6τ - 6τ²")
            print("    加速度: a(τ) = 6 - 12τ")
            print("    加加速度: j(τ) = -12")
            print()

        elif method == InterpolationMethod.CARTOON:
            print("  数学公式:")
            print("    位置: p(τ) = 6τ⁵ - 15τ⁴ + 10τ³")
            print("    速度: v(τ) = 30τ⁴ - 60τ³ + 30τ²")
            print("    加速度: a(τ) = 120τ³ - 180τ² + 60τ")
            print("    加加速度: j(τ) = 360τ² - 360τ + 60")
            print()

        print("-" * 70)
        print()

    print("关键概念:")
    print()
    print("  归一化时间 τ = t / T")
    print("    其中 t 是当前时间，T 是总运动时长")
    print("    τ 的范围是 [0, 1]")
    print()
    print("  位置 p(τ): 描述运动的轨迹")
    print("  速度 v(τ): 位置的一阶导数，描述运动快慢")
    print("  加速度 a(τ): 位置的二阶导数，描述速度变化")
    print("  加加速度 j(τ): 位置的三阶导数，描述加速度变化")
    print()
    print("推荐使用:")
    print("  ⭐ MIN_JERK - 90% 的场景，最平滑自然")
    print("  EASE_IN_OUT - 表情动作，柔和效果")
    print("  LINEAR - 仅用于简单定位测试")
    print("  CARTOON - 夸张效果，特殊场景")
    print()
    print("=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reachy Mini 插值方法理论可视化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 显示完整对比图
  python interpolation_theory.py

  # 仅显示位置曲线
  python interpolation_theory.py --position-only

  # 保存图像
  python interpolation_theory.py --save curves.png

  # 显示理论说明
  python interpolation_theory.py --theory
        """
    )

    parser.add_argument(
        '--position-only',
        action='store_true',
        help='仅显示位置曲线'
    )
    parser.add_argument(
        '--save',
        type=str,
        default=None,
        help='保存图像到指定路径'
    )
    parser.add_argument(
        '--theory',
        action='store_true',
        help='显示理论说明'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='不显示窗口（仅保存）'
    )

    args = parser.parse_args()

    # 显示理论说明
    if args.theory:
        print_theory()
        if not args.save and not args.no_display:
            print("\n按 Enter 继续显示可视化...")
            input()

    # 检查依赖
    try:
        import matplotlib
    except ImportError:
        print("Error: matplotlib 未安装")
        print("请安装: pip install matplotlib")
        sys.exit(1)

    # 创建可视化
    visualizer = InterpolationVisualizer()

    # 绘制对比图
    if not args.no_display:
        visualizer.plot_comparison(
            position_only=args.position_only,
            save_path=args.save
        )
    elif args.save:
        # 仅保存，不显示
        visualizer.plot_comparison(
            position_only=args.position_only,
            save_path=args.save
        )
        print("图像已保存，程序退出")


if __name__ == "__main__":
    main()
