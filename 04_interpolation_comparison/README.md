# Demo 4: Reachy Mini 插值方法对比

通过可视化对比和实际运动演示，帮助理解不同插值方法对机器人运动平滑度的影响。直观展示线性、最小加加速度、缓入缓出、卡通效果等插值方法的差异。

## 功能特性

- **四种插值方法对比**: LINEAR、MIN_JERK、EASE_IN_OUT、CARTOON
- **轨迹可视化**: 实时绘制位置、速度、加速度曲线
- **并排对比**: 同时展示多种插值方法的运动效果
- **理论解释**: 每种方法的数学原理和适用场景
- **交互式演示**: 可调参数实时查看效果变化
- **机器人实际运动**: 在真实机器人上对比不同方法

## 插值方法详解

### 1. LINEAR (线性插值)

**数学原理**: 匀速运动
```
p(t) = p₀ + (p₁ - p₀) × (t / T)
```

**特点**:
- 位置：线性变化
- 速度：恒定
- 加速度：0（在起点/终点有突变）

**适用场景**: 简单定位、不需要平滑的场景

---

### 2. MIN_JERK (最小加加速度) ⭐ 推荐

**数学原理**: 最小化加加速度的 7 次多项式
```
p(t) = p₀ + (p₁ - p₀) × [10τ³ - 15τ⁴ + 6τ⁵]
其中 τ = t / T
```

**特点**:
- 位置：平滑过渡
- 速度：平滑启动和停止
- 加速度：连续无突变
- 加加速度：最小化

**适用场景**: **大多数机器人运动**（默认推荐）

---

### 3. EASE_IN_OUT (缓入缓出)

**数学原理**: 3 次多项式（S形曲线）
```
p(t) = p₀ + (p₁ - p₀) × [3τ² - 2τ³]
其中 τ = t / T
```

**特点**:
- 位置：S 形曲线
- 速度：两端慢、中间快
- 加速度：连续

**适用场景**: 需要柔和效果的表情动作

---

### 4. CARTOON (卡通效果)

**数学原理**: 夸张的 5 次多项式
```
p(t) = p₀ + (p₁ - p₀) × [6τ⁵ - 15τ⁴ + 10τ³]
其中 τ = t / T
```

**特点**:
- 位置：明显的 S 形
- 速度：两端很慢、中间很快
- 加加速度：较大

**适用场景**: 夸张的卡通表情、趣味动作

---

## 快速开始

### 安装依赖

```bash
pip install reachy-mini numpy matplotlib
```

### 基本使用

```bash
# 1. 理论可视化（无需机器人）
python interpolation_theory.py

# 2. 机器人对比演示（需要机器人）
python interpolation_demo.py

# 3. 交互式调参演示
python interpolation_demo.py --interactive

# 4. 单个方法详细分析
python interpolation_demo.py --method MIN_JERK --analyze
```

## 演示模式

### 模式 1: 理论可视化

无需机器人，纯理论分析：

```bash
python interpolation_theory.py
```

**展示内容**:
- 四种方法的位置曲线对比
- 速度曲线对比
- 加速度曲线对比
- 加加速度曲线对比
- 数学公式说明

---

### 模式 2: 并排对比

同时展示两种方法的实际运动：

```bash
# 对比 LINEAR vs MIN_JERK
python interpolation_demo.py --compare LINEAR MIN_JERK

# 对比所有方法
python interpolation_demo.py --compare-all

# 指定运动时长
python interpolation_demo.py --compare-all --duration 2.0
```

---

### 模式 3: 单个方法分析

深入分析单个方法：

```bash
# 分析 MIN_JERK 方法
python interpolation_demo.py --method MIN_JERK --analyze

# 指定运动参数
python interpolation_demo.py --method EASE_IN_OUT --duration 1.5 --pitch 30
```

---

### 模式 4: 交互式演示

实时调整参数：

```bash
python interpolation_demo.py --interactive
```

**可调参数**:
- 插值方法
- 运动时长
- 运动幅度
- 是否显示曲线

---

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--method` | 插值方法: LINEAR/MIN_JERK/EASE_IN_OUT/CARTOON | MIN_JERK |
| `--compare` | 对比两种方法: `--compare M1 M2` | - |
| `--compare-all` | 对比所有方法 | - |
| `--duration` | 运动时长（秒）| 1.0 |
| `--pitch` | 俯仰角变化（度）| 20 |
| `--yaw` | 偏航角变化（度）| 0 |
| `--analyze` | 详细分析模式 | - |
| `--interactive` | 交互模式 | - |
| `--no-plot` | 不显示曲线图 | - |
| `--backend` | 媒体后端 | default |

## 运动特性对比表

| 特性 | LINEAR | MIN_JERK | EASE_IN_OUT | CARTOON |
|------|--------|----------|-------------|---------|
| **平滑度** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **速度连续** | ❌ | ✅ | ✅ | ✅ |
| **加速度连续** | ❌ | ✅ | ✅ | ✅ |
| **加加速度最小** | ❌ | ✅ | ❌ | ❌ |
| **计算复杂度** | 低 | 中 | 低 | 中 |
| **适用场景** | 简单定位 | **通用推荐** | 柔和动作 | 夸张效果 |
| **运动时长** | 最快 | 正常 | 正常 | 较慢 |

## 曲线特征

### 位置曲线

```
位置
  │
p₁─┼────────●  MIN_JERK, EASE_IN_OUT, CARTOON
  │       ╱
  │     ╱
  │   ╱
  │ ╱        ←────── LINEAR (直线)
  │╱
p₀─┼─────────────────→ 时间
  │              T
```

### 速度曲线

```
速度
  │
  │    ╱╲    ←──── MIN_JERK (平滑)
  │   ╱  ╲
  │  ╱    ╲
  │ ╱      ╲  ←──── EASE_IN_OUT (三角形)
  │╱        ╲
  └────────────→ 时间

  │
  │────────── ←──── LINEAR (恒定速度)
  │
```

### 加速度曲线

```
加速度
  │
  │    ╱╲    ←──── MIN_JERK (单峰平滑)
  │   ╱  ╲
  │  ╱    ╲
  │ ╱      ╲
  │╱        ╲
  └────────────→ 时间

  │    │    │
  │────    ─────  ←──── LINEAR (起点/终点突变)
```

## 使用场景建议

### 推荐使用 MIN_JERK 的场景

- ✅ **日常运动**（90% 的场景）
- ✅ 精确定位
- ✅ 抓取/放置操作
- ✅ 多轴协调运动
- ✅ 长距离运动

### 推荐使用 LINEAR 的场景

- ✅ 快速定位（不关心平滑）
- ✅ 简单点对点运动
- ✅ 测试/调试

### 推荐使用 EASE_IN_OUT 的场景

- ✅ 表情动作（眨眼、微笑等）
- ✅ 柔和的社交动作
- ✅ 需要柔和效果的场景

### 推荐使用 CARTOON 的场景

- ✅ 卡通表情
- ✅ 趣味互动
- ✅ 夸张的惊讶表情
- ✅ 娱乐演示

## 代码示例

### 基础用法

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
from reachy_mini.utils.interpolation import InterpolationTechnique

with ReachyMini() as mini:
    # 目标姿态：抬头 20 度
    target = create_head_pose(pitch=20, degrees=True)

    # 使用不同插值方法
    mini.goto_target(
        head=target,
        duration=1.0,
        method=InterpolationTechnique.MIN_JERK  # 推荐默认
    )
```

### 对比不同方法

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
from reachy_mini.utils.interpolation import InterpolationTechnique
import time

with ReachyMini() as mini:
    target = create_head_pose(yaw=30, degrees=True)

    methods = [
        InterpolationTechnique.LINEAR,
        InterpolationTechnique.MIN_JERK,
        InterpolationTechnique.EASE_IN_OUT,
    ]

    for method in methods:
        print(f"使用 {method} 方法...")

        # 先回到中心
        mini.goto_target(
            head=create_head_pose(),
            duration=0.5,
            method=InterpolationTechnique.MIN_JERK
        )
        time.sleep(1)

        # 执行运动
        mini.goto_target(
            head=target,
            duration=1.0,
            method=method
        )
        time.sleep(1.5)

        # 回到中心
        mini.goto_target(
            head=create_head_pose(),
            duration=1.0,
            method=method
        )
        time.sleep(1.5)
```

### 获取插值轨迹

```python
from reachy_mini.utils.interpolation import minimum_jerk, time_trajectory
import numpy as np

start = np.array([0.0, 0.0, 0.0])
end = np.array([10.0, 20.0, 30.0])
duration = 2.0

# 创建插值函数
interpolation_func = minimum_jerk(start, end, duration)

# 获取轨迹点（每 0.01 秒）
trajectory = []
t = 0
while t <= duration:
    position = interpolation_func(t)
    trajectory.append(position)
    t += 0.01

# trajectory 包含完整运动轨迹
```

## 理论背景

### 为什么需要插值？

机器人的运动如果直接跳转（set_target），会产生：
- ❌ 突变的速度
- ❌ 无限大的加速度
- ❌ 机械震动
- ❌ 电机过载

插值方法解决了这些问题：
- ✅ 平滑的速度变化
- ✅ 连续的加速度
- ✅ 减少机械磨损
- ✅ 更自然的运动

### 最小加加速度原理

**加加速度 (Jerk)** = 加速度的变化率

最小加加速度轨迹的特点：
1. 加速度连续（无突变）
2. 加加速度最小化
3. 运动最平滑
4. 人体自然运动也遵循此原理

**7 次多项式的推导**：
```
边界条件:
- p(0) = p₀,  p(T) = p₁           (位置)
- v(0) = 0,  v(T) = 0             (速度)
- a(0) = 0,  a(T) = 0             (加速度)

满足以上 6 个边界条件的最低次多项式是 5 次，
但最小化加加速度得到的是 7 次多项式。
```

## 可视化界面

### 理论可视化窗口

```
┌─────────────────────────────────────┐
│   插值方法理论对比                   │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │      位置曲线对比           │   │
│  │  ───── LINEAR               │   │
│  │  ╱╲╲╱ MIN_JERK             │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │      速度曲线对比           │   │
│  │  ───────── LINEAR           │   │
│  │   ╱╲╱╲╱  MIN_JERK          │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │    加速度曲线对比           │   │
│  │  ││    ││  LINEAR (突变)    │   │
│  │   ╱╲╱╲╱    MIN_JERK        │   │
│  └─────────────────────────────┘   │
│                                     │
│  [保存图像] [关闭]                  │
└─────────────────────────────────────┘
```

### 机器人演示窗口

```
┌─────────────────────────────────────┐
│   机器人插值运动演示                 │
├─────────────────────────────────────┤
│                                     │
│  方法: MIN_JERK                     │
│  时长: 1.0 秒                       │
│  状态: 运动中...                    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │      实时位置曲线           │   │
│  │         ● (当前点)          │   │
│  │        ╱                    │   │
│  │       ╱                     │   │
│  │      ╱                      │   │
│  └─────────────────────────────┘   │
│                                     │
│  进度: ■■■■■■■■░░ 80%             │
│                                     │
│  [下一方法] [退出]                  │
└─────────────────────────────────────┘
```

## 常见问题

**Q: 哪种插值方法最好？**
A: **MIN_JERK** 是大多数场景的最佳选择，它提供了最平滑的运动。

**Q: LINEAR 方法什么时候用？**
A: 仅用于快速定位或不关心平滑度的场景。日常使用不推荐。

**Q: 为什么我的机器人运动有震动？**
A:
1. 检查是否使用了 LINEAR 方法
2. 尝试增加 duration（减慢速度）
3. 确认使用 MIN_JERK 方法

**Q: 如何让运动更柔和？**
A:
1. 使用 EASE_IN_OUT 方法
2. 增加 duration
3. 减小运动幅度

**Q: CARTOON 方法适合什么？**
A: 适合需要夸张效果的场景，如卡通表情、趣味互动。不建议用于常规运动。

**Q: 可以自定义插值方法吗？**
A: 可以！使用 `time_trajectory()` 函数自定义时间轨迹。

## 技术细节

### 插值函数

SDK 提供的插值函数位于 `reachy_mini.utils.interpolation`：

```python
from reachy_mini.utils.interpolation import (
    minimum_jerk,           # 最小加加速度插值
    linear_pose_interpolation,  # 位姿线性插值
    InterpolationTechnique, # 插值方法枚举
    time_trajectory,        # 时间轨迹生成
)
```

### 轨迹计算流程

```
1. 定义起点和终点
   ↓
2. 选择插值方法
   ↓
3. 生成时间轨迹 τ(t)
   ↓
4. 计算位置 p(t) = p₀ + (p₁-p₀) × τ(t)
   ↓
5. 发送运动命令到机器人
```

### 性能对比

| 方法 | 计算时间 | 内存占用 | 适用性 |
|------|----------|----------|--------|
| LINEAR | 最快 | 最小 | 简单场景 |
| MIN_JERK | 快 | 小 | **通用** |
| EASE_IN_OUT | 快 | 小 | 表情动作 |
| CARTOON | 中等 | 小 | 特殊效果 |

## 依赖

- Python 3.8+
- reachy-mini
- numpy
- matplotlib (用于可视化)

## 系统要求

- Reachy Mini 机器人（用于机器人演示）
- 或仅运行理论可视化（无需机器人）

## 注意事项

1. **运动范围**: 确保目标姿态在机器人运动范围内
2. **运动时长**: 过短的时长可能导致震动（建议 ≥ 0.5s）
3. **方法选择**: 大多数情况使用 MIN_JERK 即可
4. **安全性**: 首次运行建议使用较小的运动幅度

## 扩展实验

### 实验 1: 时长影响

```bash
# 测试不同时长的效果
for duration in 0.5 1.0 1.5 2.0; do
    python interpolation_demo.py --method MIN_JERK --duration $duration
done
```

### 实验 2: 幅度影响

```bash
# 测试不同幅度的效果
for pitch in 10 20 30 40; do
    python interpolation_demo.py --method MIN_JERK --pitch $pitch
done
```

### 实验 3: 方法对比

```bash
# 对比所有方法
python interpolation_demo.py --compare-all
```

## 相关 Demo

- [Demo 2: 滑块控制](../demo2_slider_control/) - 手动控制体验
- [Demo 3: 物体追踪](../demo3_object_tracking/) - 实际应用
- [Demo 6: 声源追踪](../demo6_sound_tracking/) - 平滑追踪

## 参考资源

- **最小加加速度轨迹**: https://en.wikipedia.org/wiki/Jerk_(physics)
- **插值方法**: https://en.wikipedia.org/wiki/Interpolation
- **轨迹规划**: https://en.wikipedia.org/wiki/Trajectory_planning
