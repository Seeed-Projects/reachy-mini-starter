<div align="center">

# 🤖 Reachy Mini Starter Kit

**基于官方 API 的 Reachy Mini 机器人 Python 开发框架**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

提供基础控制接口和完整示例代码的 Python 开发框架

**中文** | [English](README.md)

</div>

---

## ✨ 特性

- 🎯 **统一配置管理** - 一处配置，全局使用
- 🎮 **完整基础 Demo** - 音频控制、身体旋转、头部动作、视频流
- 📚 **详细开发文档** - 完整的 API 参考和中英文使用指南
- 🚀 **AI 扩展就绪** - 为后续 Agent 和 LLM 集成预留扩展接口

---

## 📁 项目结构

```
reachy-mini-starter/
├── src/                          # 核心库
│   ├── connection.py             # 连接管理
│   ├── config.py                 # 配置管理
│   ├── logger.py                 # 日志系统
│   └── utils.py                  # 工具函数
├── demos/                        # 基础控制演示
│   ├── config_loader.py          # 配置加载器
│   ├── robot_config.yaml.template # 配置模板
│   ├── 01_basic_audio_control/   # 🔊 音频控制
│   ├── 02_basic_body_rotation/   # 🔄 身体旋转
│   ├── 03_basic_nod_head/        # 🫡 点头动作
│   ├── 04_basic_shake_head/      # 📢 摇头动作
│   ├── 05_webrtc_video_stream/   # 📹 WebRTC 视频流
│   ├── 06_zenoh_basic_control/   # ⚡ Zenoh 协议控制
│   ├── 07_audio_player/          # 🎵 本地音频播放器
│   ├── 08_audio_stream_api/      # 🎶 REST API 音频流服务
│   ├── 09_mic_stream_to_pc/      # 🎙️ 麦克风流传输到 PC
│   ├── 10_vision_algorithms/     # 👁️ OpenCV 视觉算法（人脸/运动/边缘/颜色/角点检测）
│   ├── 11_yolo_robot_control/    # 🤖 YOLO 检测 + Zenoh 机器人控制
│   ├── 12_antenna_angle_monitoring/ # 📡 天线舵机角度监控
│   ├── 13_head_look_around/      # 👀 头部环视运动
│   ├── 14_head_track_red_object/ # 🎯 头部追踪红色物体
│   ├── 15_web_realtime_control/  # 🌐 网页实时控制
│   ├── 16_bidirectional_audio/   # 🎙️🔊 双向音频服务
│   ├── 17_web_remote_camera/     # 🌐 网页版遥控摄像头
│   └── 18_webrtc_to_http_stream/ # 📡 WebRTC 转 MJPEG 视频流
├── docs/                         # 文档
│   ├── API_REFERENCE_CN.md       # API 参考文档（中文）
│   ├── USAGE_GUIDE_CN.md         # 使用指南（中文）
│   ├── NETWORK_GUIDE_CN.md       # 网络配置（中文）
│   ├── GSTREAMER_CN.md           # GStreamer 安装指南（中文）
│   ├── API_REFERENCE.md          # API 参考文档（English）
│   ├── USAGE_GUIDE.md            # 使用指南（English）
│   ├── NETWORK_GUIDE.md          # 网络配置（English）
│   └── GSTREAMER.md              # GStreamer 安装指南（English）
├── configs/                      # 配置文件目录
├── scripts/                      # 工具脚本
└── requirements.txt              # 依赖包
```

---

## 🚀 快速开始

### 前置要求

- Python 3.7+
- Reachy Mini 机器人（已连接同一网络）

### 安装与配置

```bash
# 克隆仓库
git clone https://github.com/yourusername/reachy-mini-starter.git
cd reachy-mini-starter

# 安装依赖
pip install -r requirements.txt

# 创建配置文件
cp demos/robot_config.yaml.template demos/robot_config.yaml

# 编辑配置文件，修改机器人 IP 地址
# vim demos/robot_config.yaml  (或使用你喜欢的编辑器)
```

**配置文件内容 (`demos/robot_config.yaml`)：**
```yaml
robot:
  ip: "10.42.0.75"    # 修改为你的机器人实际 IP
  port: 8000
```

### 运行 Demo

```bash
# 🎵 音频控制 - 扬声器/麦克风音量调节
python demos/01_basic_audio_control/test_audio_control.py

# 🔄 身体旋转 - 底座左右转动 (±160°)
python demos/02_basic_body_rotation/test_body_rotation.py

# 🫡 点头动作 - 头部上下运动
python demos/03_basic_nod_head/test_nod_head.py

# 📢 摇头动作 - 头部左右转动
python demos/04_basic_shake_head/test_shake_head.py

# 📹 WebRTC 视频流 - 接收机器人视频/音频流
python3 demos/05_webrtc_video_stream/05.py --signaling-host 10.42.0.75

# ⚡ Zenoh 控制 - 通过 Zenoh 协议进行低延迟控制
python3 demos/06_zenoh_basic_control/test_zenoh_control.py

# 🎵 音频播放器 - 播放本地/在线音频文件（运行在机器人上）
python3 demos/07_audio_player/audio_player.py --file /path/to/audio.wav

# 🎶 音频流 API 服务 - 启动 REST API 服务（运行在机器人上）
python3 demos/08_audio_stream_api/audio_stream_server.py

# 🎙️ 麦克风流传输 - 将麦克风音频推流到 PC（服务端运行在机器人上）
# 第一步：在 Reachy Mini 上启动服务端
python3 demos/09_mic_stream_to_pc/bidirectional_audio_server.py

# 第二步：在 PC 上接收流
python3 demos/09_mic_stream_to_pc/receive_mic_stream.py

# 📡 天线角度监控 - 通过 REST API 查询天线舵机角度
python demos/12_antenna_angle_monitoring/test_antenna_rest.py

# 👀 头部环视 - 头部环视运动
python demos/13_head_look_around/13.py

# 🎯 追踪红色物体 - 头部追踪红色物体运动
python demos/14_head_track_red_object/14.py

# 🎙️🔊 双向音频 - 将机器人麦克风音频推流到 PC（服务端运行在机器人上）
# 第一步：在 Reachy Mini 上启动服务端
python3 demos/16_bidirectional_audio/bidirectional_audio_server.py

# 第二步：在 PC 上接收流
python3 demos/16_bidirectional_audio/receive_mic_stream.py

# 🌐 网页版遥控摄像头 - 通过浏览器控制机器人头部
python3 demos/17_web_remote_camera/server.py

# 📡 WebRTC 转 MJPEG 视频流 - 在浏览器中观看机器人视频
python3 demos/18_webrtc_to_http_stream/18.py --signaling-host 10.42.0.75
```

---

## 📖 配置说明

所有 Demo 共用 `demos/robot_config.yaml` 配置文件，只需配置一次即可。

配置文件已加入 `.gitignore`，不会被提交到仓库，保护隐私信息。

---

## 🔌 API 接口覆盖

### REST API (已实现 ✅)

| 接口 | 方法 | 说明 | Demo |
|:----|:-----|:-----|:-----|
| `/move/goto` | POST | 平滑运动到目标 | [身体旋转](demos/02_basic_body_rotation)、[点头](demos/03_basic_nod_head)、[摇头](demos/04_basic_shake_head) |
| `/move/set_target` | POST | 立即设置目标 | - |
| `/move/goto_joint_positions` | POST | 关节空间运动 | - |
| `/move/stop` | POST | 停止运动 | 所有运动 Demo |
| `/motors/set_mode/{mode}` | POST | 设置电机模式 | 所有运动 Demo |
| `/volume/current` | GET | 获取扬声器音量 | [音频控制](demos/01_basic_audio_control) |
| `/volume/set` | POST | 设置扬声器音量 | [音频控制](demos/01_basic_audio_control) |
| `/volume/test-sound` | POST | 播放测试音 | [音频控制](demos/01_basic_audio_control) |
| `/volume/microphone/current` | GET | 获取麦克风增益 | [音频控制](demos/01_basic_audio_control) |
| `/volume/microphone/set` | POST | 设置麦克风增益 | [音频控制](demos/01_basic_audio_control) |
| `/state/present_antenna_joint_positions` | GET | 获取天线角度 | [天线监控](demos/12_antenna_angle_monitoring) |
| `/state/full` | GET | 获取完整状态 | [天线监控](demos/12_antenna_angle_monitoring) |
| `/ws/signaling` | WS | WebRTC 信令 | [视频流](demos/05_webrtc_video_stream) |

### WebSocket (已实现 ✅)

| 接口 | 说明 | Demo |
|:----|:-----|:-----|
| `/move/ws/set_target` | 实时控制 (60Hz+) | ⏳ 计划中 |
| `/state/ws/full` | 状态流 | ⏳ 计划中 |
| `/move/ws/updates` | 运动事件 | ⏳ 计划中 |

### Zenoh (已实现 ✅)

| Topic | 说明 | Demo |
|:-----|:-----|:-----|
| `reachy_mini/command` | 命令接口 | [Zenoh 控制](demos/06_zenoh_basic_control) |

### BLE (计划中 ⏳)

| 命令 | 说明 | Demo |
|:----|:-----|:-----|
| PIN 验证 | 身份验证 | ⏳ 计划中 |
| 状态查询 | 获取设备状态 | ⏳ 计划中 |
| 热点重置 | 重置网络 | ⏳ 计划中 |

### ROS2 (计划中 ⏳)

> **注意**：这是社区开发的 ROS2 中间件，用于将原生接口转换为 ROS2 topic，非官方接口。

| Topic | 消息类型 | 说明 | Demo |
|-------|----------|------|------|
| `/reachy_mini/head_command` | `geometry_msgs/PoseStamped` | 头部姿态命令 | ⏳ 计划中 |
| `/reachy_mini/joint_command` | `sensor_msgs/JointState` | 关节位置命令 | ⏳ 计划中 |
| `/reachy_mini/joint_states` | `sensor_msgs/JointState` | 当前关节状态 | ⏳ 计划中 |
| `/reachy_mini/audio/play` | `std_msgs/String` | 播放音频文件 | ⏳ 计划中 |
| `/reachy_mini/audio/volume` | `std_msgs/UInt8` | 扬声器音量 (0-100) | ⏳ 计划中 |

---

## 🎯 Demo 说明

| Demo | 功能 | API 接口 |
|:----:|------|----------|
| 🔊 **音频控制** | 扬声器/麦克风音量调节与测试 | `/api/volume/*` |
| 🔄 **身体旋转** | 底座左右旋转控制 (±160°) | `/api/move/goto`、`/api/motors/*` |
| 🫡 **点头动作** | 头部俯仰运动 | `/api/move/goto`、`/api/motors/*` |
| 📢 **摇头动作** | 头部偏航运动 | `/api/move/goto`、`/api/motors/*` |
| 📹 **WebRTC 视频** | 实时视频/音频流接收 | `/ws/signaling` |
| ⚡ **Zenoh 控制** | 低延迟协议控制 | `reachy_mini/command` |
| 🎵 **音频播放器** | 播放本地/在线音频文件（机器人上） | N/A（运行在机器人上） |
| 🎶 **音频流 API** | REST API 远程音频控制与实时推流 | 自定义 API（端口 8001） |
| 🎙️ **麦克风流** | 将机器人麦克风音频推流到 PC | WebSocket（端口 8002） |
| 👁️ **视觉算法** | OpenCV 视觉算法（人脸/运动/边缘/颜色/角点） | N/A（仅 PC） |
| 🤖 **YOLO + 控制** | YOLO 检测 + Zenoh 机器人控制 | `reachy_mini/command` |
| 📡 **天线监控** | 通过 REST API 查询天线舵机角度 | `/api/state/*` |
| 👀 **头部环视** | 头部环视运动 | `/api/move/goto` |
| 🎯 **追踪红色物体** | 头部追踪红色物体运动 | `/api/move/goto` |
| 🎙️🔊 **双向音频** | 双向音频服务 | WebSocket（端口 8002） |
| 🌐 **网页实时控制** | 通过浏览器控制机器人头部运动 | WebSocket + REST API |
| 🌐 **网页版遥控摄像头** | 网页版遥控摄像头控制 | WebSocket + REST API |
| 📡 **WebRTC 转 MJPEG** | 在浏览器中观看机器人视频流 | MJPEG HTTP 流 |

---

## 📚 文档

### 中文文档

- 📘 [API 接口开发指南](docs/API_REFERENCE_CN.md) - 完整的 REST API 参考文档
- 📗 [使用修改指南](docs/USAGE_GUIDE_CN.md) - 详细的使用说明和调试方法
- 📙 [连接配网指南](docs/NETWORK_GUIDE_CN.md) - 网络连接配置步骤
- 📺 [GStreamer 安装指南](docs/GSTREAMER_CN.md) - WebRTC 视频流安装配置

### English Documentation

- 📘 [API Reference Guide](docs/API_REFERENCE.md) - Complete REST API reference
- 📗 [Usage and Debugging Guide](docs/USAGE_GUIDE.md) - Detailed usage instructions
- 📙 [Network Configuration Guide](docs/NETWORK_GUIDE.md) - Network setup steps
- 📺 [GStreamer Installation Guide](docs/GSTREAMER.md) - WebRTC video streaming setup

---

## 🗺️ 开发路线

当前版本为基础控制接口，后续计划：

- [x] 👁️ **视觉系统** - 摄像头视觉识别能力
- [x] 🤖 **YOLO 集成** - 物体检测与机器人控制
- [x] 📡 **状态监控** - 天线舵机角度查询
- [ ] 🤖 **Agent 集成** - 结合 AI Agent 实现智能决策和行为规划
- [ ] 🧠 **LLM 集成** - 接入大语言模型实现自然语言交互
- [ ] 🎤 **语音交互** - 集成语音识别和语音合成
- [ ] 😊 **情感表达** - 基于内部状态的情感化动作表达

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

---

<div align="center">

**用 ❤️ 为 Reachy Mini 社区构建**

**由 [Seeed Studio](https://www.seeedstudio.com/) 提供支持**

</div>
