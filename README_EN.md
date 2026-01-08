<div align="center">

# 🤖 Reachy Mini Lite

**Reachy Mini Robot Example Code Collection**

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Concise and practical Reachy Mini robot control examples to help you get started with robotics development quickly.

[中文文档](README.md) | [Quick Start](#-quick-start)

</div>

---

## 📖 Project Overview

This project is a collection of example code for the **Reachy Mini** robot, covering 6 core application scenarios: camera interaction, motion control, object tracking, interpolation motion, audio processing, and sound source localization.

> **Reachy Mini** is a small humanoid robot equipped with movable parts such as a head and antennas, supporting flexible control through Python SDK.

---

## 🎯 Features

- **📷 Camera Interaction** - Get robot's camera view with click interaction
- **🎛️ Motion Control** - Real-time robot posture control via GUI interface
- **🎯 Object Tracking** - YOLO-based visual object tracking
- **📈 Interpolation Motion** - Experience different motion trajectory control
- **🔊 Audio Processing** - Robot audio playback and recording
- **🎧 Sound Localization** - Microphone array-based sound source tracking
- **🔧 Easy to Extend** - Clear code structure for easy secondary development

---

## 📁 Project Structure

```
reachymini_lite/
├── 01_camera_display/              # 📷 Camera display
│   ├── camera_display_basic.py     # Basic version
│   ├── camera_display_optimized.py # Optimized version (recommended)
│   └── README.md
│
├── 02_slider_control/              # 🎛️ Slider motion control
│   ├── slider_control.py           # GUI control panel
│   └── README.md
│
├── 03_object_tracking/             # 🎯 YOLO object tracking
│   ├── object_tracking.py          # Basic tracking
│   ├── object_tracking_v2.py       # Enhanced tracking
│   └── README.md
│
├── 04_interpolation_comparison/    # 📈 Interpolation comparison
│   ├── interpolation_demo.py       # Interactive demo
│   ├── interpolation_theory.py     # Theory visualization
│   └── README.md
│
├── 05_audio_streaming/             # 🔊 Audio processing
│   ├── audio_streaming.py          # Audio playback
│   ├── mic_recording.py            # Microphone recording
│   └── README.md
│
├── 06_sound_tracking/              # 🎧 Sound localization
│   ├── sound_tracking.py           # Sound source tracking
│   └── README.md
│
├── docs/                           # 📚 Documentation
├── reachy_mini/                    # Reachy Mini SDK
├── pyproject.toml                  # Project configuration
├── uv.lock                         # Dependency lock file
├── LICENSE                         # Open source license
├── README.md                       # Chinese documentation
└── README_EN.md                    # English documentation
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python Environment**: Python 3.12 or higher
2. **Hardware**: Reachy Mini robot
3. **Start daemon**:
   ```bash
   reachy-mini-daemon start
   ```

### Install Dependencies

Using uv (recommended):
```bash
# Install uv
pip install uv

# Install project dependencies
uv sync
```

Or using pip:
```bash
pip install reachy-mini opencv-python ultralytics numpy
```

---

## 📖 Demo Details

### 01 - 📷 Camera Display

[View Details →](01_camera_display/README.md)

| File | Description | Recommended For |
|------|-------------|-----------------|
| [`camera_display_basic.py`](01_camera_display/camera_display_basic.py) | Basic version, default resolution | Understanding basics |
| [`camera_display_optimized.py`](01_camera_display/camera_display_optimized.py) | Optimized version, configurable resolution | Practical use (recommended) |

```bash
# Optimized version (recommended, default 640x480 resolution)
python 01_camera_display/camera_display_optimized.py

# Custom window size
python 01_camera_display/camera_display_optimized.py --window-scale 0.3

# Higher resolution
python 01_camera_display/camera_display_optimized.py --resolution 1280x720
```

**Main Features**:
- Real-time display of Reachy Mini camera feed
- Mouse click interaction: click anywhere on the screen, robot looks at that point
- Press `q` to exit the program

---

### 02 - 🎛️ Slider Motion Control

[View Details →](02_slider_control/README.md)

```bash
python 02_slider_control/slider_control.py
```

**Main Features**:
- Head position control: X (front/back), Y (left/right), Z (up/down)
- Head angle control: Roll, Pitch, Yaw
- Antenna control: Left antenna, right antenna angles
- Body control: Body Yaw
- One-click reset function

---

### 03 - 🎯 YOLO Object Tracking

[View Details →](03_object_tracking/README.md)

| File | Description |
|------|-------------|
| [`object_tracking.py`](03_object_tracking/object_tracking.py) | Basic object tracking |
| [`object_tracking_v2.py`](03_object_tracking/object_tracking_v2.py) | Enhanced tracking (more stable) |

```bash
# Basic version
python 03_object_tracking/object_tracking.py

# Enhanced version (recommended)
python 03_object_tracking/object_tracking_v2.py
```

**Main Features**:
- Detect and track objects using YOLOv8
- Robot head automatically follows the target
- Support for multiple object categories

---

### 04 - 📈 Interpolation Comparison

[View Details →](04_interpolation_comparison/README.md)

| File | Description |
|------|-------------|
| [`interpolation_demo.py`](04_interpolation_comparison/interpolation_demo.py) | Interactive interpolation demo |
| [`interpolation_theory.py`](04_interpolation_comparison/interpolation_theory.py) | Theory visualization |

```bash
# Interactive demo
python 04_interpolation_comparison/interpolation_demo.py

# Theory visualization
python 04_interpolation_comparison/interpolation_theory.py
```

**Main Features**:
- Compare effects of different interpolation methods
- Visualize motion trajectories
- Understand minimum jitter vs linear motion

---

### 05 - 🔊 Audio Processing

[View Details →](05_audio_streaming/README.md)

| File | Description |
|------|-------------|
| [`audio_streaming.py`](05_audio_streaming/audio_streaming.py) | Robot audio playback |
| [`mic_recording.py`](05_audio_streaming/mic_recording.py) | Microphone array recording |

```bash
# Audio playback
python 05_audio_streaming/audio_streaming.py

# Recording test
python 05_audio_streaming/mic_recording.py
```

**Main Features**:
- Play audio through the robot
- Record microphone array audio
- Real-time audio stream processing

---

### 06 - 🎧 Sound Localization

[View Details →](06_sound_tracking/README.md)

```bash
python 06_sound_tracking/sound_tracking.py
```

**Main Features**:
- DOA (Direction of Arrival) based sound source estimation
- Robot head automatically turns toward sound source
- Real-time visualization of sound direction

---

## 💻 Code Examples

### Get Camera Frame

```python
from reachy_mini import ReachyMini

with ReachyMini() as mini:
    # Get current frame
    frame = mini.media.get_frame()
```

### Control Robot Motion

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

with ReachyMini() as mini:
    # Set head pose (degrees, millimeters)
    mini.goto_target(
        head=create_head_pose(z=10, roll=0, degrees=True, mm=True),
        duration=1.0
    )
```

### Make Robot Look at Point

```python
with ReachyMini() as mini:
    # Look at image coordinates (x, y)
    mini.look_at_image(x, y, duration=0.3)
```

### Object Tracking

```python
from ultralytics import YOLO
import cv2

# Load YOLO model
model = YOLO('yolov8n.pt')

# Detect objects
results = model(frame)
```

---

## 📚 Related Resources

- [Reachy Mini Official Documentation](https://pollen-robotics.github.io/reachy-mini/)
- [API Reference](https://pollen-robotics.github.io/reachy-mini/api/)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Feel free to open an issue if you have any questions or suggestions!**

Made with ❤️ for Reachy Mini

</div>
