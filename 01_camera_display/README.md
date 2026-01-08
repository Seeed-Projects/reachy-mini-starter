# 01 - 摄像头画面显示

展示如何使用 Reachy Mini 获取摄像头画面并实现点击交互功能。当您点击图像上的任意位置时，Reachy Mini 会转向看向该点。

## 文件说明

| 文件 | 说明 | 推荐场景 |
|------|------|----------|
| `camera_display_basic.py` | 基础版，使用默认分辨率 | 了解基本原理 |
| `camera_display_optimized.py` | 优化版，可配置分辨率和窗口大小 | 实际使用（推荐） |

## 快速开始

### 优化版（推荐）

```bash
# 默认配置：640x480 分辨率，50% 窗口大小（最流畅）
python camera_display_optimized.py

# 调整窗口大小
python camera_display_optimized.py --window-scale 0.3

# 更高质量
python camera_display_optimized.py --resolution 1280x720
```

### 基础版

```bash
python camera_display_basic.py
```

## 功能特点

- 实时显示 Reachy Mini 的摄像头画面
- 鼠标点击交互：点击画面任意位置，机器人看向该点
- 支持 `q` 键退出程序
- 优化版支持自定义分辨率和窗口大小

## 参数说明（优化版）

| 参数 | 选项 | 默认值 | 说明 |
|------|------|--------|------|
| `--backend` | default, gstreamer, webrtc | default | 媒体后端类型 |
| `--resolution` | 640x480, 800x600, 1280x720 | 640x480 | 捕获分辨率 |
| `--window-scale` | 0.1 - 1.0 | 0.5 | 窗口缩放比例 |

## 性能对比

| 版本 | 分辨率 | 数据量 | 流畅度 |
|------|--------|--------|--------|
| 基础版 | 1920x1080 | 100% | 一般 |
| 优化版（默认） | 640x480 | ~14% | **流畅** |

## 操作说明

1. 运行脚本后，会弹出一个显示摄像头画面的窗口
2. **点击画面上的任意位置**，Reachy Mini 会转向看向该点
3. 按 **`q`** 键退出程序

## 前置条件

```bash
# 安装依赖
pip install reachy-mini opencv-python

# 启动守护进程
reachy-mini-daemon start
```

## 代码示例

```python
# 获取摄像头画面
frame = reachy_mini.media.get_frame()

# 使机器人看向图像坐标 (x, y)
reachy_mini.look_at_image(x, y, duration=0.3)

# 设置分辨率（优化版）
reachy_mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
reachy_mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
```
