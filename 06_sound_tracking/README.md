# Demo 6: Reachy Mini 声源定位追踪

基于声源定位 (DoA) 的智能交互演示。Reachy Mini 会实时检测声源方向，并自动转向说话的人，实现自然的听觉-视觉交互体验。

## 功能特性

- **实时声源定位**: 使用麦克风阵列检测声源方向
- **自动追踪**: 机器人自动转向声源，实现"听声辨位"
- **平滑运动**: 使用 PID 控制器实现流畅的头部运动
- **视觉反馈**: 实时显示声源方向、追踪状态和头部角度
- **多种追踪模式**: 支持头部追踪、身体追踪、混合追踪
- **智能过滤**: 过滤短暂噪声，只响应持续语音
- **交互反馈**: 追踪时天线动作提供视觉反馈

## 快速开始

### 安装依赖

```bash
pip install reachy-mini opencv-python numpy
```

### 基本使用

```bash
# 默认模式：仅头部追踪
python sound_tracking.py

# 头部 + 身体追踪（更大转向范围）
python sound_tracking.py --mode body

# 混合模式（头部 + 身体协调）
python sound_tracking.py --mode hybrid

# 调整追踪灵敏度
python sound_tracking.py --sensitivity high

# 调整响应速度（更快的反应）
python sound_tracking.py --speed 0.2
```

## 追踪模式对比

| 模式 | 头部运动 | 身体运动 | 转向范围 | 推荐场景 |
|------|----------|----------|----------|----------|
| **head** (默认) | ✓ | ✗ | ±35° | 小范围追踪 |
| **body** | ✗ | ✓ | ±160° | 大范围追踪 |
| **hybrid** | ✓ | ✓ | ±160° | 全方位追踪 |

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | 追踪模式: head/body/hybrid | head |
| `--backend` | 媒体后端: default/gstreamer/webrtc | default |
| `--sensitivity` | 灵敏度: low/medium/high | medium |
| `--speed` | 响应速度（秒）| 0.5 |
| `--window-scale` | 窗口缩放（0.1-1.0）| 0.7 |
| `--no-antenna` | 禁用天线反馈 | - |
| `--pid-p` | PID 比例系数 | 0.6 |
| `--pid-i` | PID 积分系数 | 0.01 |
| `--pid-d` | PID 微分系数 | 0.3 |
| `--min-duration` | 最小语音时长（秒）| 0.3 |

## 工作原理

### 声源定位 (DoA)

Reachy Mini 使用麦克风阵列（如 ReSpeaker）进行声源定位：

```
┌─────────────────────────────────┐
│         麦克风阵列               │
│    ◉───────────◉               │
│      (DoA: 45°)                 │
└─────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│    声源方向检测                  │
│  - 0° = 左侧                    │
│  - 90° = 前方                   │
│  - 180° = 右侧                  │
└─────────────────────────────────┘
```

### 坐标系转换

DoA 角度需要转换为机器人偏航角：

```python
# DoA 角度定义: 0=左, 90=前, 180=右
# 机器人偏航: 正值=左转, 负值=右转
robot_yaw = (90 - doa_angle)  # 度
robot_yaw_rad = math.radians(robot_yaw)
```

### PID 控制器

使用 PID 控制器实现平滑追踪：

```
误差 = 目标角度 - 当前角度
输出 = Kp×误差 + Ki×积分误差 + Kd×误差变化率
```

## 界面说明

```
┌─────────────────────────────────────┐
│   Reachy Mini Sound Tracking        │
│                                     │
│   Tracking: ACTIVE  ← 追踪状态      │
│   Source: 45° LEFT  ← 声源方向      │
│   Head Yaw: 40°      ← 当前角度     │
│                                     │
│        [机器人摄像头画面]            │
│                                     │
│   ━━━━━━━━━━━━━━━━                 │
│        ↑                            │
│    声源方向指示器                    │
│                                     │
│   Voice Activity: ■■■■□  ← 音量    │
└─────────────────────────────────────┘
```

## 状态指示

| 状态 | 说明 | 显示 |
|------|------|------|
| **IDLE** | 待机，未检测到语音 | 灰色 |
| **DETECTING** | 检测到语音，正在分析 | 黄色 |
| **TRACKING** | 正在追踪声源 | 绿色 |
| **LOST** | 声源丢失 | 红色 |

## 使用场景

### 1. 会议室追踪

在会议环境中追踪发言人：

```bash
python sound_tracking.py --mode hybrid --sensitivity medium
```

### 2. 展览互动

在展览中与访客互动：

```bash
python sound_tracking.py --mode head --speed 0.3
```

### 3. 演示助手

作为演讲助手，面向听众：

```bash
python sound_tracking.py --mode body --sensitivity low
```

## PID 调优建议

### 响应过慢

- 增大 `--pid-p` (如 0.8-1.0)
- 减小 `--speed` (如 0.2-0.3)

### 追踪震荡

- 减小 `--pid-p` (如 0.4-0.5)
- 增大 `--pid-d` (如 0.4-0.5)

### 稳态误差

- 增大 `--pid-i` (如 0.02-0.05)

### 快速移动目标

- 增大 `--pid-d` (如 0.4-0.6)
- 减小 `--speed` (如 0.2)

## 灵敏度设置

| 灵敏度 | 最小语音时长 | 适用场景 |
|--------|--------------|----------|
| **low** | 0.5 秒 | 安静环境、长对话 |
| **medium** | 0.3 秒 | 一般环境（默认）|
| **high** | 0.15 秒 | 嘈杂环境、快速响应 |

## 技术架构

```
┌─────────────────┐
│  麦克风阵列      │
│  (ReSpeaker)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ get_DoA()       │ ← 获取声源方向
│ (angle, speech) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  语音活动检测    │ ← 过滤噪声
│  (VAD)          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  角度转换        │ ← DoA → 机器人角度
│  (坐标系转换)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PID 控制器      │ ← 平滑运动
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ goto_target()   │ ← 机器人运动
│ set_target()    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  视觉反馈        │ ← 显示状态
│  (天线动作)      │
└─────────────────┘
```

## 常见问题

**Q: 机器人不转向声源？**
A:
1. 确认使用带麦克风阵列的机器人（如 ReSpeaker）
2. 检查声源是否在有效范围内（前方 ±90°）
3. 尝试提高灵敏度 `--sensitivity high`
4. 确认 daemon 服务正在运行

**Q: 追踪不稳定，频繁抖动？**
A:
1. 减小 PID-P 参数（如 0.4）
2. 增大 PID-D 参数（如 0.4）
3. 降低灵敏度 `--sensitivity low`
4. 增加最小语音时长 `--min-duration 0.5`

**Q: 响应太慢？**
A:
1. 减小响应速度 `--speed 0.2`
2. 增大 PID-P 参数（如 0.8）
3. 提高灵敏度 `--sensitivity high`

**Q: 转向角度不够？**
A:
1. 使用 `--mode body` 或 `--mode hybrid`
2. 身体模式支持 ±160° 转向

**Q: 天线不动作？**
A:
1. 检查是否使用 `--no-antenna` 参数
2. 确认机器人天线电机已启用

## 代码示例

### 基础声源追踪

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import math

with ReachyMini() as mini:
    while True:
        # 获取声源方向
        doa_result = mini.media.get_DoA()

        if doa_result is not None:
            angle, speech_detected = doa_result

            if speech_detected:
                # 转换为机器人偏航角
                angle_deg = math.degrees(angle)
                robot_yaw = (90 - angle_deg)

                # 控制机器人转向
                pose = create_head_pose(yaw=robot_yaw, degrees=True)
                mini.goto_target(head=pose, duration=0.5)
```

### 带天线反馈的追踪

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import math
import time

with ReachyMini() as mini:
    tracking = False

    while True:
        doa_result = mini.media.get_DoA()

        if doa_result is not None:
            angle, speech_detected = doa_result

            if speech_detected:
                if not tracking:
                    # 开始追踪：天线抬起
                    mini.set_target(antennas=[0.5, 0.5])
                    tracking = True

                # 转向声源
                angle_deg = math.degrees(angle)
                robot_yaw = (90 - angle_deg)
                pose = create_head_pose(yaw=robot_yaw, degrees=True)
                mini.goto_target(head=pose, duration=0.3)
            else:
                if tracking:
                    # 停止追踪：天线放下
                    mini.set_target(antennas=[0, 0])
                    tracking = False

        time.sleep(0.1)
```

## 依赖

- Python 3.8+
- reachy-mini
- opencv-python
- numpy

## 系统要求

- Reachy Mini 机器人（推荐 Wireless 版本带麦克风阵列）
- 麦克风阵列（如 ReSpeaker 2-Mics Pi HAT）
- 已启动 reachy-mini-daemon 服务

## 注意事项

1. **麦克风阵列**: 声源定位需要麦克风阵列支持，单麦克风无法定位
2. **环境噪音**: 在嘈杂环境中可能降低准确性
3. **声源范围**: 最佳检测范围为前方 ±90°
4. **网络延迟**: 网络连接可能增加响应延迟
5. **运动限制**: 头部偏航限制 ±35°，使用身体模式可扩展到 ±160°

## 扩展功能

### 添加人脸识别

结合人脸识别实现声源+视觉双重追踪：

```bash
# 运行物体追踪 demo
python ../demo3_object_tracking/object_tracking.py

# 结合声源追踪，实现多模态交互
```

### 语音指令集成

集成语音识别，实现"听声 + 辨意"：

```python
# 添加语音识别
# 当检测到语音时，同时进行：
# 1. 声源定位追踪
# 2. 语音识别
# 3. 执行对应指令
```

## 相关 Demo

- [Demo 5: 音频流和录音](../demo5_audio_streaming/) - 基础音频功能
- [Demo 3: 物体追踪](../demo3_object_tracking/) - 视觉追踪
- [Demo 2: 滑块控制](../demo2_slider_control/) - 手动控制
