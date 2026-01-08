<div align="center">

# 🤖 Reachy Mini Starter Kit

**Python Development Framework for Reachy Mini Robot**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A clean, well-documented Python framework for controlling Reachy Mini robots with basic motion and audio interfaces.

[中文文档](README_EN.md) | **English**

</div>

---

## ✨ Features

- 🎯 **Unified Configuration** - Configure once, use everywhere
- 🎮 **Complete Demos** - Audio control, body rotation, head motions, video streaming
- 📚 **Comprehensive Docs** - Full API reference and usage guides in EN/CN
- 🚀 **Ready for AI** - Extensible interfaces for Agent and LLM integration

---

## 📁 Project Structure

```
reachy-mini-starter/
├── src/                          # Core library
│   ├── connection.py             # Connection management
│   ├── config.py                 # Configuration management
│   ├── logger.py                 # Logging system
│   └── utils.py                  # Utility functions
├── demos/                        # Basic control demos
│   ├── config_loader.py          # Config loader
│   ├── robot_config.yaml.template # Config template
│   ├── 01_basic_audio_control/   # 🔊 Audio control
│   ├── 02_basic_body_rotation/   # 🔄 Body rotation
│   ├── 03_basic_nod_head/        # 🫡 Nod head motion
│   ├── 04_basic_shake_head/      # 📢 Shake head motion
│   ├── 05_webrtc_video_stream/   # 📹 WebRTC video streaming
│   ├── 06_zenoh_basic_control/   # ⚡ Zenoh protocol control
│   ├── 07_audio_player/          # 🎵 Local audio player
│   ├── 08_audio_stream_api/      # 🎶 REST API audio streaming service
│   ├── 09_mic_stream_to_pc/      # 🎙️ Microphone stream to PC
│   ├── 10_vision_algorithms/     # 👁️ OpenCV vision algorithms (face/motion/edge/color/corner detection)
│   ├── 11_yolo_robot_control/    # 🤖 YOLO detection + Zenoh robot control
│   ├── 12_antenna_angle_monitoring/ # 📡 Antenna servo angle monitoring
│   ├── 13_head_look_around/      # 👀 Head look around motion
│   ├── 14_head_track_red_object/ # 🎯 Track red object with head
│   ├── 16_bidirectional_audio/   # 🎙️🔊 Bidirectional audio service
│   └── 17_web_remote_camera/     # 🌐 Web-based remote camera control
├── docs/                         # Documentation
│   ├── API_REFERENCE.md          # API reference (EN)
│   ├── USAGE_GUIDE.md            # Usage guide (EN)
│   ├── NETWORK_GUIDE.md          # Network guide (EN)
│   ├── GSTREAMER.md              # GStreamer installation (EN)
│   ├── API_REFERENCE_CN.md       # API reference (中文)
│   ├── USAGE_GUIDE_CN.md         # Usage guide (中文)
│   ├── NETWORK_GUIDE_CN.md       # Network guide (中文)
│   └── GSTREAMER_CN.md           # GStreamer 安装指南 (中文)
├── configs/                      # Configuration files
├── scripts/                      # Utility scripts
└── requirements.txt              # Dependencies
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.7+
- Reachy Mini robot (connected to same network)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/reachy-mini-starter.git
cd reachy-mini-starter

# Install dependencies
pip install -r requirements.txt

# Create configuration file
cp demos/robot_config.yaml.template demos/robot_config.yaml

# Edit the configuration with your robot's IP
# vim demos/robot_config.yaml  (or use your preferred editor)
```

**Configuration file (`demos/robot_config.yaml`):**
```yaml
robot:
  ip: "10.42.0.75"    # Change to your robot's IP
  port: 8000
```

### Run Demos

```bash
# 🎵 Audio Control - Speaker/microphone volume
python demos/01_basic_audio_control/test_audio_control.py

# 🔄 Body Rotation - Base left/right rotation (±160°)
python demos/02_basic_body_rotation/test_body_rotation.py

# 🫡 Nod Head - Head up/down motion
python demos/03_basic_nod_head/test_nod_head.py

# 📢 Shake Head - Head left/right motion
python demos/04_basic_shake_head/test_shake_head.py

# 📹 WebRTC Video Stream - Receive video/audio from robot
python3 demos/05_webrtc_video_stream/05.py --signaling-host 10.42.0.75

# ⚡ Zenoh Control - Low-latency control via Zenoh protocol
python3 demos/06_zenoh_basic_control/test_zenoh_control.py

# 🎵 Audio Player - Play local/online audio files (runs on robot)
python3 demos/07_audio_player/audio_player.py --file /path/to/audio.wav

# 🎶 Audio Stream API - Start REST API service (runs on robot)
python3 demos/08_audio_stream_api/audio_stream_server.py

# 🎙️ Microphone Stream - Stream mic audio to PC (server on robot)
# Step 1: Start server on Reachy Mini
python3 demos/09_mic_stream_to_pc/bidirectional_audio_server.py

# Step 2: Receive stream on PC
python3 demos/09_mic_stream_to_pc/receive_mic_stream.py

# 👁️ Vision Algorithms - OpenCV vision algorithms on video stream
python3 demos/10_vision_algorithms/10.py --signaling-host 10.42.0.75

# 🤖 YOLO + Robot Control - YOLO detection with Zenoh robot control
python3 demos/11_yolo_robot_control/11.py --signaling-host 10.42.0.75

# 📡 Antenna Angle Monitoring - Query antenna servo angles via REST API
python demos/12_antenna_angle_monitoring/test_antenna_rest.py

# 👀 Head Look Around - Look around with head motion
python demos/13_head_look_around/13.py

# 🎯 Track Red Object - Track red object with head motion
python demos/14_head_track_red_object/14.py

# 🎙️🔊 Bidirectional Audio - Stream mic audio from robot to PC (server on robot)
# Step 1: Start server on Reachy Mini
python3 demos/16_bidirectional_audio/bidirectional_audio_server.py

# Step 2: Receive stream on PC
python3 demos/16_bidirectional_audio/receive_mic_stream.py

# 🌐 Web Remote Camera - Control robot head via browser
python3 demos/17_web_remote_camera/server.py
```

---

## 📖 Configuration

All demos share `demos/robot_config.yaml` - configure once and use globally.

The configuration file is included in `.gitignore` to protect your private information.

---

## 🔌 API Interface Coverage

### REST API (Implemented ✅)

| Endpoint | Method | Description | Demo |
|----------|--------|-------------|------|
| `/move/goto` | POST | Smooth motion to target | [Body Rotation](demos/02_basic_body_rotation), [Nod Head](demos/03_basic_nod_head), [Shake Head](demos/04_basic_shake_head) |
| `/move/set_target` | POST | Set target immediately | - |
| `/move/goto_joint_positions` | POST | Joint space motion | - |
| `/move/stop` | POST | Stop motion | All motion demos |
| `/motors/set_mode/{mode}` | POST | Set motor mode | All motion demos |
| `/volume/current` | GET | Get speaker volume | [Audio Control](demos/01_basic_audio_control) |
| `/volume/set` | POST | Set speaker volume | [Audio Control](demos/01_basic_audio_control) |
| `/volume/test-sound` | POST | Play test sound | [Audio Control](demos/01_basic_audio_control) |
| `/volume/microphone/current` | GET | Get mic gain | [Audio Control](demos/01_basic_audio_control) |
| `/volume/microphone/set` | POST | Set mic gain | [Audio Control](demos/01_basic_audio_control) |
| `/state/present_antenna_joint_positions` | GET | Get antenna angles | [Antenna Monitoring](demos/12_antenna_angle_monitoring) |
| `/state/full` | GET | Get full state | [Antenna Monitoring](demos/12_antenna_angle_monitoring) |
| `/ws/signaling` | WS | WebRTC signaling | [Video Stream](demos/05_webrtc_video_stream) |

### WebSocket (Implemented ✅)

| Endpoint | Description | Demo |
|----------|-------------|------|
| `/move/ws/set_target` | Real-time control (60Hz+) | ⏳ Planned |
| `/state/ws/full` | State streaming | ⏳ Planned |
| `/move/ws/updates` | Motion events | ⏳ Planned |

### Zenoh (Implemented ✅)

| Topic | Description | Demo |
|-------|-------------|------|
| `reachy_mini/command` | Command interface | [Zenoh Control](demos/06_zenoh_basic_control) |

### BLE (Planned ⏳)

| Command | Description | Demo |
|---------|-------------|------|
| PIN verification | Authentication | ⏳ Planned |
| Status query | Get device status | ⏳ Planned |
| Hotspot reset | Reset network | ⏳ Planned |

### ROS2 (Planned ⏳)

> **Note**: This is a community-developed ROS2 middleware that converts native APIs to ROS2 topics, not an official interface.

| Topic | Message Type | Description | Demo |
|-------|--------------|-------------|------|
| `/reachy_mini/head_command` | `geometry_msgs/PoseStamped` | Head pose command | ⏳ Planned |
| `/reachy_mini/joint_command` | `sensor_msgs/JointState` | Joint position command | ⏳ Planned |
| `/reachy_mini/joint_states` | `sensor_msgs/JointState` | Current joint states | ⏳ Planned |
| `/reachy_mini/audio/play` | `std_msgs/String` | Audio file to play | ⏳ Planned |
| `/reachy_mini/audio/volume` | `std_msgs/UInt8` | Speaker volume (0-100) | ⏳ Planned |

---

## 🎯 Demo Overview

| Demo | Description | API Endpoints |
|:----:|:-----------|:--------------|
| 🔊 **Audio Control** | Speaker/microphone volume & testing | `/api/volume/*` |
| 🔄 **Body Rotation** | Base rotation (±160°) | `/api/move/goto`, `/api/motors/*` |
| 🫡 **Nod Head** | Head pitch motion | `/api/move/goto`, `/api/motors/*` |
| 📢 **Shake Head** | Head yaw motion | `/api/move/goto`, `/api/motors/*` |
| 📹 **WebRTC Video** | Real-time video/audio streaming | `/ws/signaling` |
| ⚡ **Zenoh Control** | Low-latency protocol control | `reachy_mini/command` |
| 🎵 **Audio Player** | Play local/online audio files (on robot) | N/A (runs on robot) |
| 🎶 **Audio Stream API** | REST API for remote audio control & streaming | Custom API (port 8001) |
| 🎙️ **Mic Stream** | Stream mic audio from robot to PC | WebSocket (port 8002) |
| 👁️ **Vision Algorithms** | OpenCV algorithms (face/motion/edge/color/corner) | N/A (PC only) |
| 🤖 **YOLO + Control** | YOLO detection + Zenoh robot control | `reachy_mini/command` |
| 📡 **Antenna Monitor** | Query antenna servo angles via REST API | `/api/state/*` |
| 👀 **Head Look Around** | Head look around motion | `/api/move/goto` |
| 🎯 **Track Red Object** | Track red object with head motion | `/api/move/goto` |
| 🎙️🔊 **Bidirectional Audio** | Bidirectional audio service via WebSocket | WebSocket (port 8002) |
| 🌐 **Web Remote Camera** | Web-based head control via browser | WebSocket + REST API |

---

## 📚 Documentation

### English

- 📘 [API Reference Guide](docs/API_REFERENCE.md) - Complete REST API reference
- 📗 [Usage and Debugging Guide](docs/USAGE_GUIDE.md) - Detailed usage instructions
- 📙 [Network Configuration Guide](docs/NETWORK_GUIDE.md) - Network setup steps
- 📺 [GStreamer Installation Guide](docs/GSTREAMER.md) - WebRTC video streaming setup

### 中文

- 📘 [API 接口开发指南](docs/API_REFERENCE_CN.md) - 完整的 REST API 参考文档
- 📗 [使用修改指南](docs/USAGE_GUIDE_CN.md) - 详细的使用说明和调试方法
- 📙 [连接配网指南](docs/NETWORK_GUIDE_CN.md) - 网络连接配置步骤
- 📺 [GStreamer 安装指南](docs/GSTREAMER_CN.md) - WebRTC 视频流安装配置

---

## 🗺️ Roadmap

Current version provides basic control interfaces. Future plans:

- [x] 👁️ **Vision System** - Camera-based visual recognition
- [x] 🤖 **YOLO Integration** - Object detection with robot control
- [x] 📡 **State Monitoring** - Antenna servo angle monitoring
- [ ] 🤖 **Agent Integration** - AI Agent for intelligent decision-making
- [ ] 🧠 **LLM Integration** - Natural language interaction
- [ ] 🎤 **Voice Interaction** - Speech recognition and synthesis
- [ ] 😊 **Emotional Expression** - Emotion-based motion expressions

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

<div align="center">

**Built with ❤️ for the Reachy Mini community**

**Powered by [Seeed Studio](https://www.seeedstudio.com/)**

</div>
