<div align="center">

# 🤖 Reachy Mini Lite

**Reachy Mini 机器人示例代码集合**

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

简洁、实用的 Reachy Mini 机器人控制示例，帮助你快速上手机器人开发。

[English Documentation](README_EN.md) | [快速开始](#-快速开始)

</div>

---

## 📖 项目简介

本项目是 **Reachy Mini** 机器人的示例代码集合，涵盖 6 个核心应用场景：摄像头交互、运动控制、目标追踪、插值运动、音频处理和声源定位。

> **Reachy Mini** 是一款小型人形机器人，配备头部、天线等可动部件，支持通过 Python SDK 进行灵活控制。

---

## 🎯 功能特性

- **📷 摄像头交互** - 获取机器人视角画面，支持点击交互
- **🎛️ 运动控制** - 通过 GUI 界面实时控制机器人姿态
- **🎯 目标追踪** - 基于 YOLO 的视觉目标追踪
- **📈 插值运动** - 体验不同的运动轨迹控制
- **🔊 音频处理** - 机器人音频播放与录音
- **🎧 声源定位** - 基于麦克风阵列的声源追踪
- **🔧 易于扩展** - 代码结构清晰，方便二次开发

---

## 📁 项目结构

```
reachymini_lite/
├── 01_camera_display/              # 📷 摄像头画面显示
│   ├── camera_display_basic.py     # 基础版本
│   ├── camera_display_optimized.py # 优化版本（推荐）
│   └── README.md
│
├── 02_slider_control/              # 🎛️ 滑块运动控制
│   ├── slider_control.py           # GUI 控制面板
│   └── README.md
│
├── 03_object_tracking/             # 🎯 YOLO 目标追踪
│   ├── object_tracking.py          # 基础追踪
│   ├── object_tracking_v2.py       # 增强版追踪
│   └── README.md
│
├── 04_interpolation_comparison/    # 📈 插值运动对比
│   ├── interpolation_demo.py       # 交互式演示
│   ├── interpolation_theory.py     # 理论可视化
│   └── README.md
│
├── 05_audio_streaming/             # 🔊 音频处理
│   ├── audio_streaming.py          # 音频播放
│   ├── mic_recording.py            # 麦克风录音
│   └── README.md
│
├── 06_sound_tracking/              # 🎧 声源定位
│   ├── sound_tracking.py           # 声源追踪
│   └── README.md
│
├── docs/                           # 📚 文档
├── reachy_mini/                    # Reachy Mini SDK
├── pyproject.toml                  # 项目配置
├── uv.lock                         # 依赖锁定文件
├── LICENSE                         # 开源许可证
├── README.md                       # 中文文档
└── README_EN.md                    # 英文文档
```

---

## 🚀 快速开始

### 前置条件

1. **Python 环境**: Python 3.12 或更高版本
2. **硬件设备**: Reachy Mini 机器人
3. **启动 Robot Server (Daemon)**

Daemon 是一个后台服务，用于处理与电机和传感器的底层通信。在使用这些脚本之前，Daemon 必须处于运行状态。

**Reachy Mini (无线版本)**: 当机器人开机时，daemon 自动运行。确保你的电脑和 Reachy Mini 在同一网络中。

**Reachy Mini Lite (USB 连接)** - 你有两种选择：
- 启动桌面应用程序
- 打开终端运行：
  ```bash
  uv run reachy-mini-daemon
  ```

**仿真模式 (无需机器人)** - 你有两种选择：
- 启动桌面应用程序
- 打开终端运行：
  ```bash
  uv run reachy-mini-daemon --sim
  ```

✅ **验证方法**: 在浏览器中打开 http://localhost:8000。如果看到 Reachy 仪表板，说明你已经准备好了！

### 安装依赖

使用 uv（推荐）：
```bash
# 安装 uv
pip install uv

# 安装项目依赖
uv sync
```

或使用 pip：
```bash
pip install reachy-mini opencv-python ultralytics numpy
```

---

## 📖 Demo 详解

### 01 - 📷 摄像头画面显示

[查看详情 →](01_camera_display/README.md)

| 文件 | 说明 | 推荐场景 |
|------|------|----------|
| [`camera_display_basic.py`](01_camera_display/camera_display_basic.py) | 基础版，默认分辨率 | 了解基本原理 |
| [`camera_display_optimized.py`](01_camera_display/camera_display_optimized.py) | 优化版，可配置分辨率 | 实际使用（推荐） |

```bash
# 优化版（推荐，默认 640x480 分辨率）
python 01_camera_display/camera_display_optimized.py

# 自定义窗口大小
python 01_camera_display/camera_display_optimized.py --window-scale 0.3

# 更高分辨率
python 01_camera_display/camera_display_optimized.py --resolution 1280x720
```

**主要功能**:
- 实时显示 Reachy Mini 摄像头画面
- 鼠标点击交互：点击画面任意位置，机器人看向该点
- 支持 `q` 键退出程序

---

### 02 - 🎛️ 滑块运动控制

[查看详情 →](02_slider_control/README.md)

```bash
python 02_slider_control/slider_control.py
```

**主要功能**:
- 头部位置控制：X (前后), Y (左右), Z (上下)
- 头部角度控制：Roll (翻滚), Pitch (俯仰), Yaw (偏航)
- 天线控制：左天线、右天线角度
- 身体控制：Body Yaw (身体偏航角)
- 一键重置功能

---

### 03 - 🎯 YOLO 目标追踪

[查看详情 →](03_object_tracking/README.md)

| 文件 | 说明 |
|------|------|
| [`object_tracking.py`](03_object_tracking/object_tracking.py) | 基础目标追踪 |
| [`object_tracking_v2.py`](03_object_tracking/object_tracking_v2.py) | 增强版追踪（更稳定） |

```bash
# 基础版
python 03_object_tracking/object_tracking.py

# 增强版（推荐）
python 03_object_tracking/object_tracking_v2.py
```

**主要功能**:
- 使用 YOLOv8 检测并追踪目标
- 机器人头部自动跟随目标移动
- 支持多种物体类别检测

---

### 04 - 📈 插值运动对比

[查看详情 →](04_interpolation_comparison/README.md)

| 文件 | 说明 |
|------|------|
| [`interpolation_demo.py`](04_interpolation_comparison/interpolation_demo.py) | 交互式插值演示 |
| [`interpolation_theory.py`](04_interpolation_comparison/interpolation_theory.py) | 理论可视化 |

```bash
# 交互式演示
python 04_interpolation_comparison/interpolation_demo.py

# 理论可视化
python 04_interpolation_comparison/interpolation_theory.py
```

**主要功能**:
- 对比不同插值方法的效果
- 可视化运动轨迹
- 理解最小抖动与直线运动

---

### 05 - 🔊 音频处理

[查看详情 →](05_audio_streaming/README.md)

| 文件 | 说明 |
|------|------|
| [`audio_streaming.py`](05_audio_streaming/audio_streaming.py) | 机器人音频播放 |
| [`mic_recording.py`](05_audio_streaming/mic_recording.py) | 麦克风阵列录音 |

```bash
# 音频播放
python 05_audio_streaming/audio_streaming.py

# 录音测试
python 05_audio_streaming/mic_recording.py
```

**主要功能**:
- 通过机器人播放音频
- 录制麦克风阵列音频
- 实时音频流处理

---

### 06 - 🎧 声源定位

[查看详情 →](06_sound_tracking/README.md)

```bash
python 06_sound_tracking/sound_tracking.py
```

**主要功能**:
- 基于 DOA (Direction of Arrival) 估计声源方向
- 机器人头部自动转向声源
- 实时可视化声源方向

---

## 💻 代码示例

### 获取摄像头画面

```python
from reachy_mini import ReachyMini

with ReachyMini() as mini:
    # 获取当前帧
    frame = mini.media.get_frame()
```

### 控制机器人运动

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

with ReachyMini() as mini:
    # 设置头部姿态（角度制，毫米）
    mini.goto_target(
        head=create_head_pose(z=10, roll=0, degrees=True, mm=True),
        duration=1.0
    )
```

### 使机器人看向特定点

```python
with ReachyMini() as mini:
    # 看向图像坐标 (x, y)
    mini.look_at_image(x, y, duration=0.3)
```

### 目标追踪

```python
from ultralytics import YOLO
import cv2

# 加载 YOLO 模型
model = YOLO('yolov8n.pt')

# 检测目标
results = model(frame)
```

---

## 📚 相关资源

- [Reachy Mini 官方文档](https://pollen-robotics.github.io/reachy-mini/)
- [API 参考手册](https://pollen-robotics.github.io/reachy-mini/api/)
- [YOLOv8 文档](https://docs.ultralytics.com/)

---

## 📄 开源许可

本项目采用 [MIT License](LICENSE) 开源许可证。

---

<div align="center">

**如有问题或建议，欢迎提 Issue！**

Made with ❤️ for Reachy Mini

</div>
