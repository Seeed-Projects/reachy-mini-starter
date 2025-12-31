# Reachy Mini Starter Kit

Python development framework for Reachy Mini robot based on official API, providing basic control interfaces and complete example code.

---

[中文版](README.md) | **English**

---

## Features

- Unified configuration management system - configure once, use globally
- Complete basic control demos covering audio, motion and other core functions
- Detailed API development documentation and usage guides
- Extension interfaces reserved for future Agent and LLM integration

## Project Structure

```
reachy-mini-starter/
├── src/                          # Core library
│   ├── connection.py             # Connection management
│   ├── config.py                 # Configuration management
│   ├── logger.py                 # Logging system
│   └── utils.py                  # Utility functions
├── demos/                        # Basic control demos
│   ├── config_loader.py          # Configuration loader
│   ├── robot_config.yaml.template # Configuration template
│   ├── 01_basic_audio_control/   # Audio control
│   ├── 02_basic_body_rotation/   # Body rotation
│   ├── 03_basic_nod_head/        # Nod head motion
│   └── 04_basic_shake_head/      # Shake head motion
├── docs/                         # Documentation
│   ├── API_REFERENCE_CN.md       # API reference (Chinese)
│   ├── USAGE_GUIDE_CN.md         # Usage guide (Chinese)
│   ├── NETWORK_GUIDE_CN.md       # Network guide (Chinese)
│   ├── API_REFERENCE.md          # API reference (English)
│   ├── USAGE_GUIDE.md            # Usage guide (English)
│   └── NETWORK_GUIDE.md          # Network guide (English)
├── configs/                      # Configuration directory
├── scripts/                      # Utility scripts
└── requirements.txt              # Dependencies
```

## Quick Start

### Prerequisites

- Python 3.7+
- Reachy Mini robot (connected to same network)

### Installation & Configuration

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create configuration file
cp demos/robot_config.yaml.template demos/robot_config.yaml

# 3. Edit configuration file, update robot IP address
vim demos/robot_config.yaml
```

Configuration file content:

```yaml
robot:
  ip: "10.42.0.75"    # Change to your robot's actual IP
  port: 8000
```

### Run Demos

```bash
# Audio control - Speaker/microphone volume adjustment
python demos/01_basic_audio_control/test_audio_control.py

# Body rotation - Base left/right rotation
python demos/02_basic_body_rotation/test_body_rotation.py

# Nod head - Head up/down motion
python demos/03_basic_nod_head/test_nod_head.py

# Shake head - Head left/right motion
python demos/04_basic_shake_head/test_shake_head.py
```

## Configuration

All demos share the `demos/robot_config.yaml` configuration file - configure only once.

The configuration file is included in `.gitignore` and will not be committed to the repository to protect private information.

## Demo Overview

| Demo | Function | API Interface |
|------|----------|---------------|
| Audio Control | Speaker/microphone volume adjustment and testing | `/api/volume/*` |
| Body Rotation | Base left/right rotation control (±160°) | `/api/move/goto` |
| Nod Head | Head pitch motion | `/api/move/goto` |
| Shake Head | Head yaw motion | `/api/move/goto` |

## Documentation

### English Documentation

- [API Reference Guide](docs/API_REFERENCE.md) - Complete REST API reference
- [Usage and Debugging Guide](docs/USAGE_GUIDE.md) - Detailed usage instructions
- [Network Configuration Guide](docs/NETWORK_GUIDE.md) - Network setup steps

### 中文文档

- [API 接口开发指南](docs/API_REFERENCE_CN.md) - 完整的 REST API 参考文档
- [使用修改指南](docs/USAGE_GUIDE_CN.md) - 详细的使用说明和修改建议
- [连接配网指南](docs/NETWORK_GUIDE_CN.md) - 网络连接配置步骤

## Roadmap

Current version provides basic control interfaces. Future plans:

- [ ] **Agent Integration** - Combine AI Agent for intelligent decision-making and behavior planning
- [ ] **LLM Integration** - Integrate Large Language Models for natural language interaction
- [ ] **Vision System** - Add camera visual recognition capabilities
- [ ] **Voice Interaction** - Integrate speech recognition and synthesis
- [ ] **Emotional Expression** - Emotional motion expression based on internal states

## License

See [LICENSE](LICENSE) file
