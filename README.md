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
- 🎮 **Complete Demos** - Audio control, body rotation, head motions
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
│   └── 04_basic_shake_head/      # 📢 Shake head motion
├── docs/                         # Documentation
│   ├── API_REFERENCE.md          # API reference (EN)
│   ├── USAGE_GUIDE.md            # Usage guide (EN)
│   ├── NETWORK_GUIDE.md          # Network guide (EN)
│   ├── API_REFERENCE_CN.md       # API reference (中文)
│   ├── USAGE_GUIDE_CN.md         # Usage guide (中文)
│   └── NETWORK_GUIDE_CN.md       # Network guide (中文)
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
```

---

## 📖 Configuration

All demos share `demos/robot_config.yaml` - configure once and use globally.

The configuration file is included in `.gitignore` to protect your private information.

---

## 🎯 Demo Overview

| Demo | Description | API Endpoint |
|:----:|-----------|--------------|
| 🔊 **Audio Control** | Speaker/microphone volume & testing | `/api/volume/*` |
| 🔄 **Body Rotation** | Base rotation (±160°) | `/api/move/goto` |
| 🫡 **Nod Head** | Head pitch motion | `/api/move/goto` |
| 📢 **Shake Head** | Head yaw motion | `/api/move/goto` |

---

## 📚 Documentation

### English

- 📘 [API Reference Guide](docs/API_REFERENCE.md) - Complete REST API reference
- 📗 [Usage and Debugging Guide](docs/USAGE_GUIDE.md) - Detailed usage instructions
- 📙 [Network Configuration Guide](docs/NETWORK_GUIDE.md) - Network setup steps

### 中文

- 📘 [API 接口开发指南](docs/API_REFERENCE_CN.md) - 完整的 REST API 参考文档
- 📗 [使用修改指南](docs/USAGE_GUIDE_CN.md) - 详细的使用说明和调试方法
- 📙 [连接配网指南](docs/NETWORK_GUIDE_CN.md) - 网络连接配置步骤

---

## 🗺️ Roadmap

Current version provides basic control interfaces. Future plans:

- [ ] 🤖 **Agent Integration** - AI Agent for intelligent decision-making
- [ ] 🧠 **LLM Integration** - Natural language interaction
- [ ] 👁️ **Vision System** - Camera-based visual recognition
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

</div>
