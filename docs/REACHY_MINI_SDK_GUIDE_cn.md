# Reachy Mini SDK 完整使用指南

## 目录

1. [摄像头系统详解](#1-摄像头系统详解)
2. [远程连接配置](#2-远程连接配置)
3. [服务器启动参数详解](#3-服务器启动参数详解)
4. [完整代码示例](#4-完整代码示例)

---

## 1. 摄像头系统详解

### 1.1 核心文件结构

```
src/reachy_mini/media/
├── camera_base.py          # 摄像头抽象基类
├── camera_opencv.py        # OpenCV 后端实现
├── camera_gstreamer.py     # GStreamer 后端实现
├── camera_constants.py     # 摄像头常量和规格定义
├── camera_utils.py         # 摄像头自动检测工具
└── media_manager.py        # 媒体管理器（统一接口）
```

### 1.2 支持的摄像头硬件

| 摄像头类型 | VID | PID | 分辨率支持 |
|-----------|-----|-----|-----------|
| **Reachy Mini Lite** | 0x38FB | 0x1002 | 1920x1080@60fps, 3840x2592@30fps |
| **Arducam 12MP** | 0x0C45 | 0x636D | 2304x1296@30fps, 4608x2592@10fps |
| **旧版 Raspberry Pi Camera** | 0x1BCF | 0x28C4 | 同 Lite 版本 |
| **Reachy Mini Wireless** | - | - | 1920x1080@30fps (通过 WebRTC) |
| **通用 USB 摄像头** | - | - | 1280x720@30fps (回退选项) |

### 1.3 摄像头自动检测逻辑

[camera_utils.py](src/reachy_mini/media/camera_utils.py#L18-L66) 中的 `find_camera()` 函数按优先级检测：

```python
1. Reachy Mini Lite 摄像头 (VID: 0x38FB, PID: 0x1002)
2. 旧版 Raspberry Pi Camera (VID: 0x1BCF, PID: 0x28C4)
3. Arducam 12MP (VID: 0x0C45, PID: 0x636D)
4. 通用摄像头（回退到 /dev/video0）
```

### 1.4 摄像头后端对比

| 特性 | OpenCV | GStreamer | WebRTC |
|------|--------|-----------|--------|
| **使用场景** | 本地 Lite 版本 | Linux 无线版（本地） | 远程客户端 |
| **硬件加速** | 无 | VAAPI/NVJPEG | 取决于浏览器 |
| **延迟** | 中 | 低 | 中 |
| **跨平台** | 是 | 仅 Linux | 是 |
| **分辨率设置** | 运行时 | 运行时 | 固定 |
| **Unix Socket 支持** | 否 | 是 | 否 |

### 1.5 分辨率选项

[camera_constants.py](src/reachy_mini/media/camera_constants.py#L11-L36) 定义的所有分辨率：

```python
class CameraResolution(Enum):
    R1280x720at30fps   # 720p HD
    R1280x720at60fps   # 720p 60fps
    R1536x864at40fps   # 中等分辨率
    R1600x1200at30fps  # 4:3 比例
    R1920x1080at30fps  # 1080p HD
    R1920x1080at60fps  # 1080p 60fps
    R2304x1296at30fps  # Arducam 高分辨率
    R3072x1728at10fps  # 高像素
    R3264x2448at30fps  # 8MP @ 30fps
    R3264x2448at10fps  # 8MP @ 10fps
    R3840x2160at30fps  # 4K UHD
    R3840x2160at10fps  # 4K @ 10fps
    R3840x2592at30fps  # 10MP @ 30fps
    R3840x2592at10fps  # 10MP @ 10fps
    R4608x2592at10fps  # Arducam 最高分辨率
```

### 1.6 相机内参和畸变系数

每种摄像头都预标定了相机内参矩阵 **K** 和畸变系数 **D**：

```python
# Reachy Mini Lite 相机参数
K = [[821.515, 0.0,    962.241],
     [0.0,    820.830, 542.459],
     [0.0,    0.0,    1.0]]

D = [-2.944e-02, 6.005e-02, 3.578e-06, -2.965e-04, -3.792e-02]
```

分辨率变化时，内参矩阵会自动按比例调整。

### 1.7 基本摄像头使用

```python
from reachy_mini import ReachyMini

# 创建实例，SDK 会自动检测并初始化摄像头
with ReachyMini() as reachy:
    # 获取一帧图像 (BGR 格式, numpy array)
    frame = reachy.media.get_frame()

    if frame is not None:
        print(f"Frame shape: {frame.shape}")  # (height, width, 3)
        print(f"Frame dtype: {frame.dtype}")   # uint8

        # 保存图像
        import cv2
        cv2.imwrite("capture.jpg", frame)

        # 获取相机参数
        camera = reachy.media.camera
        print(f"Resolution: {camera.resolution}")      # (width, height)
        print(f"Framerate: {camera.framerate}")        # fps
        print(f"Camera Matrix K:\n{camera.K}")
        print(f"Distortion D:\n{camera.D}")
```

### 1.8 设置摄像头分辨率

```python
from reachy_mini import ReachyMini
from reachy_mini.media.camera_constants import CameraResolution

with ReachyMini() as reachy:
    # 设置分辨率为 1080p@30fps
    reachy.media.camera.set_resolution(CameraResolution.R1920x1080at30fps)

    # 或设置为 720p@60fps
    reachy.media.camera.set_resolution(CameraResolution.R1280x720at60fps)
```

### 1.9 媒体后端选择

```python
from reachy_mini import ReachyMini

# 不同媒体后端配置
backends = {
    # OpenCV + SoundDevice (Lite 默认)
    "default": "本地 OpenCV 摄像头 + SoundDevice 音频",

    # GStreamer (Linux 无线版本地)
    "gstreamer": "GStreamer 摄像头 + 音频",

    # WebRTC (无线版远程客户端)
    "webrtc": "通过 WebRTC 流式传输",

    # 禁用媒体
    "no_media": "完全不使用摄像头和音频"
}

with ReachyMini(media_backend="default") as reachy:
    frame = reachy.media.get_frame()
```

### 1.10 音频功能

```python
from reachy_mini import ReachyMini

with ReachyMini() as reachy:
    # 播放声音
    reachy.media.play_sound("wake_up.wav")

    # 开始录音
    reachy.media.start_recording()

    # 获取音频样本
    audio_sample = reachy.media.get_audio_sample()

    # 停止录音
    reachy.media.stop_recording()

    # 获取声音方向 (Direction of Arrival)
    doa = reachy.media.get_DoA()
    if doa is not None:
        angle, speech_detected = doa
        print(f"Sound angle: {angle:.2f} rad, Speech: {speech_detected}")
```

---

## 2. 远程连接配置

### 2.1 网络架构概览

Reachy Mini 使用 **Zenoh** 协议进行机器人控制通信：

```
┌─────────────────┐          ┌─────────────────┐
│   PC 客户端      │          │  Reachy Mini    │
│                 │          │   服务器端       │
│                 │          │                 │
│  ZenohClient    │◄────────►│  ZenohServer    │
│  (peer mode)    │  7447    │  (router mode)  │
│                 │          │                 │
└─────────────────┘          └─────────────────┘
       IP: 任意                   IP: 10.42.0.75
```

### 2.2 连接模式说明

| 模式 | 说明 | Zenoh 配置 | 使用场景 |
|------|------|-----------|---------|
| **auto** | 优先本地，失败后网络发现 | 先 client 后 peer | 开发调试 |
| **localhost_only** | 仅连接本地服务器 | mode: client | 本地开发 |
| **network** | 网络发现模式 | mode: peer + scouting | 局域网控制 |

### 2.3 Zenoh 配置详解

#### 服务器端 ([zenoh_server.py](src/reachy_mini/io/zenoh_server.py#L40-L84))

```python
# localhost_only = True (默认)
{
    "listen": {"endpoints": ["tcp/localhost:7447"]},
    "scouting": {
        "multicast": {"enabled": False},
        "gossip": {"enabled": False}
    }
}

# localhost_only = False (--no-localhost-only)
{
    "listen": {"endpoints": ["tcp/0.0.0.0:7447"]},  # 所有接口
    "scouting": {
        "multicast": {"enabled": True},   # 多播发现
        "gossip": {"enabled": True}       # 节点间传播
    },
    "connect": {"endpoints": []}          # 接受任意连接
}
```

#### 客户端端 ([zenoh_client.py](src/reachy_mini/io/zenoh_client.py#L36-L57))

```python
# localhost_only = True
{
    "mode": "client",
    "connect": {"endpoints": ["tcp/localhost:7447"]}
}

# localhost_only = False (network 模式)
{
    "mode": "peer",                       # 对等模式
    "scouting": {
        "multicast": {"enabled": True},   # 自动发现
        "gossip": {"enabled": True}
    },
    "connect": {"endpoints": []}          # 不强制指定服务器
}
```

### 2.4 远程连接完整流程

#### 步骤 1: 服务器端启动（Reachy Mini 设备）

```bash
# 在 Reachy Mini 设备 (IP: 10.42.0.75) 上运行
python -m reachy_mini.daemon.app.main \
    --wireless-version \
    --no-localhost-only \
    --fastapi-host 0.0.0.0 \
    --fastapi-port 8000
```

**关键参数说明：**
- `--wireless-version`: 启用无线版本功能
- `--no-localhost-only`: **核心参数**，允许局域网访问
- `--fastapi-host 0.0.0.0`: Web API 监听所有接口

#### 步骤 2: 配置防火墙

```bash
# 在 Reachy Mini 设备上运行
sudo ufw allow 7447/tcp  # Zenoh 控制端口
sudo ufw allow 8000/tcp  # FastAPI Web 端口
```

#### 步骤 3: 客户端连接（PC）

```python
from reachy_mini import ReachyMini

# 方式 1: 使用 network 模式（推荐）
with ReachyMini(
    connection_mode="network",
    timeout=10.0
) as reachy:
    # 控制机器人
    reachy.goto_target(head={"z": 10}, duration=1.0)

    # 获取摄像头画面
    frame = reachy.media.get_frame()

    # 获取关节位置
    head_joints, antenna_joints = reachy.get_current_joint_positions()
    print(f"Head: {head_joints}")
    print(f"Antennas: {antenna_joints}")

# 方式 2: 使用 auto 模式（自动回退）
with ReachyMini(
    connection_mode="auto",  # 先尝试本地，失败后尝试网络
    timeout=10.0
) as reachy:
    # 同上
    pass
```

### 2.5 网络发现机制

Zenoh 使用以下机制自动发现设备：

1. **多播 (Multicast)**: 在局域网广播发现消息
2. **Gossip**: 节点间信息传播
3. **Peer 模式**: 客户端和服务器平等连接

**注意事项：**
- 确保两台设备在同一网段
- 网络必须支持多播（企业网络可能禁用）
- `robot_name`（默认 `reachy_mini`）用作 Zenoh topic 命名空间

### 2.6 端口使用总结

| 端口 | 协议 | 用途 | 服务器端 | 客户端 |
|------|------|------|---------|--------|
| **7447** | TCP | Zenoh 机器人控制 | 监听 | 连接 |
| **8000** | HTTP | FastAPI Web API | 监听 | 访问 |
| **8443** | TCP | WebRTC 信令（无线版） | 监听 | 连接 |

### 2.7 故障排查

| 问题 | 可能原因 | 解决方法 |
|------|----------|---------|
| 连接超时 | 防火墙阻止 | 开放端口 7447, 8000 |
| 无法发现设备 | 不在同一网段 | 检查 IP 配置 |
| 媒体流失败 | 后端不匹配 | 检查 `media_backend` 设置 |
| 多播失败 | 网络禁用多播 | 使用交换机或配置路由 |

---

## 3. 服务器启动参数详解

### 3.1 启动命令模板

```bash
python -m reachy_mini.daemon.app.main [选项]
```

### 3.2 完整参数列表

#### 版本控制参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--wireless-version` | flag | `False` | 启用无线版本模式（额外路由） |
| `--desktop-app-daemon` | flag | `False` | 桌面应用守护进程模式 |

#### 网络配置参数（远程控制关键）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--localhost-only` | flag | `True` (无线版 `False`) | **限制仅本地访问** |
| `--no-localhost-only` | flag | - | **允许局域网访问** |
| `--fastapi-host` | string | `0.0.0.0` | FastAPI 监听地址 |
| `--fastapi-port` | int | `8000` | FastAPI 端口 |
| `--robot-name` | string | `reachy_mini` | 机器人名称（Zenoh prefix） |

#### 机器人控制参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-p, --serialport` | string | `auto` | 串口（自动检测或手动指定如 `/dev/ttyACM0`） |
| `--hardware-config-filepath` | string | 内置路径 | 硬件配置 YAML 文件路径 |
| `--wake-up-on-start` | flag | `True` | 启动时自动唤醒机器人 |
| `--no-wake-up-on-start` | flag | - | 启动时不唤醒 |
| `--goto-sleep-on-stop` | flag | `True` | 停止时自动休眠 |
| `--no-goto-sleep-on-stop` | flag | - | 停止时不休眠 |

#### 仿真模式参数

| 参数 | 说明 |
|------|------|
| `--sim` | 使用 MuJoCo 仿真模式 |
| `--mockup-sim` | 轻量级仿真（无需 MuJoCo） |
| `--scene` | 仿真场景名称（默认: `empty`） |
| `--headless` | MuJoCo 无 GUI 模式 |

#### 运动学参数

| 参数 | 类型 | 默认值 | 可选值 |
|------|------|--------|-------|
| `--kinematics-engine` | string | `AnalyticalKinematics` | `Placo`, `NN`, `AnalyticalKinematics` |
| `--check-collision` | flag | `False` | 启用碰撞检测 |

#### 媒体与 WebSocket 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--websocket-uri` | string | `None` | WebSocket URI（例: `ws://localhost:8000`） |
| `--stream-media` | flag | `False` | 通过 WebSocket 流式传输媒体 |
| `--deactivate-audio` | flag | - | 禁用音频（默认启用） |

#### 守护进程控制参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--autostart` | flag | `True` | 自动启动守护进程 |
| `--no-autostart` | flag | - | 不自动启动 |
| `--timeout-health-check` | float | `None` | 健康检查超时（秒） |

#### 日志参数

| 参数 | 类型 | 默认值 | 可选值 |
|------|------|--------|-------|
| `--log-level` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `--log-file` | string | `None` | 日志文件路径 |

### 3.3 常用启动配置示例

#### 配置 1: 本地开发（Lite 版本）

```bash
python -m reachy_mini.daemon.app.main \
    --log-level DEBUG \
    --autostart
```

#### 配置 2: 局域网远程控制

```bash
python -m reachy_mini.daemon.app.main \
    --wireless-version \
    --no-localhost-only \
    --fastapi-host 0.0.0.0 \
    --fastapi-port 8000
```

#### 配置 3: 仿真模式

```bash
python -m reachy_mini.daemon.app.main \
    --sim \
    --scene minimal \
    --headless
```

#### 配置 4: 生产环境（完整配置）

```bash
python -m reachy_mini.daemon.app.main \
    --wireless-version \
    --no-localhost-only \
    --kinematics-engine Placo \
    --check-collision \
    --log-level INFO \
    --timeout-health-check 30.0 \
    --goto-sleep-on-stop
```

### 3.4 无线版本额外功能

使用 `--wireless-version` 时，额外启用以下路由：

| 路由 | 功能 |
|------|------|
| `/cache` | 缓存管理 |
| `/update` | 系统更新 |
| `/wifi_config` | WiFi 配置 |
| `/logs` | 日志查看 |

### 3.5 服务器状态检查

启动成功后，可以访问：

- **Dashboard**: `http://10.42.0.75:8000/`
- **Settings** (无线版): `http://10.42.0.75:8000/settings`
- **Logs** (无线版): `http://10.42.0.75:8000/logs`

---

## 4. 完整代码示例

### 4.1 基本远程控制示例

```python
"""
Reachy Mini 远程控制完整示例
演示：连接、移动、获取摄像头画面、获取传感器数据
"""

from reachy_mini import ReachyMini
import numpy as np
import cv2

def main():
    # 连接到局域网内的 Reachy Mini
    # 服务器端需使用: --no-localhost-only 启动
    with ReachyMini(
        connection_mode="network",  # 使用网络发现模式
        timeout=10.0,               # 连接超时 10 秒
        media_backend="default"     # 使用默认媒体后端
    ) as reachy:

        print("✅ 已连接到 Reachy Mini")

        # ===== 1. 获取摄像头画面 =====
        frame = reachy.media.get_frame()
        if frame is not None:
            print(f"📷 摄像头分辨率: {frame.shape}")

            # 保存第一帧
            cv2.imwrite("reachy_camera.jpg", frame)
            print("💾 已保存图像到 reachy_camera.jpg")

        # ===== 2. 移动机器人头部 =====
        print("🎯 移动到初始位置...")
        reachy.goto_target(
            head=np.eye(4),           # 单位矩阵 = 初始位置
            antennas=[0.0, 0.0],      # 天线归零
            duration=2.0
        )

        # ===== 3. 向上看 20 度 =====
        print("👆 向上看...")
        import time
        time.sleep(0.5)

        from scipy.spatial.transform import Rotation as R
        pose_up = np.eye(4)
        pose_up[:3, :3] = R.from_euler('xyz', [20, 0, 0], degrees=True).as_matrix()
        reachy.goto_target(head=pose_up, duration=1.0)

        # ===== 4. 获取关节位置 =====
        head_joints, antenna_joints = reachy.get_current_joint_positions()
        print(f"🦾 头部关节: {head_joints}")
        print(f"📡 天线角度: {antenna_joints}")

        # ===== 5. 获取当前头部姿态 =====
        head_pose = reachy.get_current_head_pose()
        print(f"📍 头部姿态矩阵:\n{head_pose}")

        # ===== 6. 检查 IMU 数据（仅无线版） =====
        if reachy.imu is not None:
            print("🧭 IMU 数据可用:")
            print(f"   加速度: {reachy.imu['accelerometer']}")
            print(f"   陀螺仪: {reachy.imu['gyroscope']}")
            print(f"   四元数: {reachy.imu['quaternion']}")
        else:
            print("⚠️  IMU 不可用（Lite 版本）")

        # ===== 7. 播放声音 =====
        print("🔊 播放唤醒声音...")
        reachy.media.play_sound("wake_up.wav")

        # ===== 8. 使用 look_at 功能 =====
        # 看向图像中的特定点
        print("👀 看向图像中心...")
        if reachy.media.camera is not None:
            width, height = reachy.media.camera.resolution
            reachy.look_at_image(
                u=width // 2,    # 水平中心
                v=height // 2,   # 垂直中心
                duration=1.0
            )

        # ===== 9. 看向 3D 空间中的点 =====
        print("🎯 看向前方 0.5 米处...")
        reachy.look_at_world(
            x=0.5,  # X: 前
            y=0.0,  # Y: 左
            z=0.0,  # Z: 上
            duration=1.0
        )

        print("✨ 演示完成！")

if __name__ == "__main__":
    main()
```

### 4.2 摄像头高级使用示例

```python
"""
摄像头高级功能示例
演示：分辨率设置、相机参数使用、图像处理
"""

from reachy_mini import ReachyMini
from reachy_mini.media.camera_constants import CameraResolution
import cv2
import numpy as np

def camera_advanced_demo():
    with ReachyMini() as reachy:
        camera = reachy.media.camera

        if camera is None:
            print("❌ 摄像头未初始化")
            return

        # ===== 1. 查看可用分辨率 =====
        specs = camera.camera_specs
        print(f"📷 摄像头型号: {specs.name}")
        print(f"可用分辨率:")
        for res in specs.available_resolutions:
            print(f"  - {res.name}")

        # ===== 2. 切换分辨率 =====
        print("\n🔄 切换到 720p@60fps...")
        camera.set_resolution(CameraResolution.R1280x720at60fps)
        print(f"当前分辨率: {camera.resolution}")
        print(f"当前帧率: {camera.framerate} fps")

        # ===== 3. 获取相机内参 =====
        K = camera.K
        D = camera.D
        print(f"\n📐 相机内参矩阵 K:\n{K}")
        print(f"🔧 畸变系数 D: {D}")

        # ===== 4. 畸变校正示例 =====
        frame = reachy.media.get_frame()
        if frame is not None:
            h, w = frame.shape[:2]

            # 畸变校正
            newcameramtx, roi = cv2.getOptimalNewCameraMatrix(
                K, D, (w, h), 1, (w, h)
            )
            undistorted = cv2.undistort(frame, K, D, None, newcameramtx)

            # 保存对比图
            comparison = np.hstack([frame, undistorted])
            cv2.imwrite("distortion_comparison.jpg", comparison)
            print("💾 已保存畸变校正对比图")

        # ===== 5. 实时捕获 =====
        print("\n📹 实时捕获 10 帧...")
        for i in range(10):
            frame = reachy.media.get_frame()
            if frame is not None:
                print(f"帧 {i+1}: {frame.shape}, dtype={frame.dtype}")

        # ===== 6. 分辨率性能测试 =====
        resolutions = [
            CameraResolution.R1280x720at30fps,
            CameraResolution.R1920x1080at30fps,
        ]

        print("\n⚡ 分辨率性能测试:")
        for res in resolutions:
            camera.set_resolution(res)
            import time

            # 测量获取 10 帧的时间
            start = time.time()
            for _ in range(10):
                reachy.media.get_frame()
            elapsed = time.time() - start

            fps = 10 / elapsed
            print(f"  {res.name}: 实际 {fps:.1f} fps")

if __name__ == "__main__":
    camera_advanced_demo()
```

### 4.3 录制和回放示例

```python
"""
录制和回放机器人动作示例
"""

from reachy_mini import ReachyMini
import numpy as np
import time

def recording_demo():
    with ReachyMini(connection_mode="network") as reachy:

        # ===== 1. 录制动作 =====
        print("🔴 开始录制动作 (5 秒)...")
        reachy.start_recording()

        start_time = time.time()
        while time.time() - start_time < 5.0:
            # 执行一些动作
            pose = np.eye(4)
            pose[0, 3] = 0.1 * np.sin(time.time() * 2)  # 左右移动
            reachy.set_target(head=pose)
            time.sleep(0.1)

        recorded_data = reachy.stop_recording()
        print(f"✅ 录制完成，共 {len(recorded_data)} 帧")

        # ===== 2. 查看录制数据 =====
        print("\n📊 录制数据示例:")
        for i, frame in enumerate(recorded_data[:3]):
            print(f"帧 {i}:")
            print(f"  时间: {frame['time']:.2f}")
            if 'head' in frame:
                print(f"  头部姿态: {frame['head'][:3][:3]}")  # 部分矩阵
            if 'antennas' in frame:
                print(f"  天线: {frame['antennas']}")

        # ===== 3. 回放动作 =====
        print("\n▶️  回放动作...")

        # 回到起始位置
        first_frame = recorded_data[0]
        if 'head' in first_frame:
            start_pose = np.array(first_frame['head'])
            reachy.goto_target(head=start_pose, duration=1.0)

        time.sleep(1)

        # 逐帧回放
        for frame in recorded_data:
            if 'head' in frame:
                pose = np.array(frame['head'])
                reachy.set_target(head=pose)
            if 'antennas' in frame:
                antennas = frame['antennas']
                reachy.set_target(antennas=antennas)

            # 根据录制时间控制回放速度
            time.sleep(0.05)  # 20fps 回放

        print("✅ 回放完成")

if __name__ == "__main__":
    recording_demo()
```

---

## 附录

### A. 文件参考

| 文件 | 行号 | 功能描述 |
|------|------|---------|
| [camera_base.py](src/reachy_mini/media/camera_base.py) | 21-101 | 摄像头抽象基类 |
| [camera_opencv.py](src/reachy_mini/media/camera_opencv.py) | 22-90 | OpenCV 摄像头实现 |
| [camera_gstreamer.py](src/reachy_mini/media/camera_gstreamer.py) | 40-200+ | GStreamer 摄像头实现 |
| [camera_utils.py](src/reachy_mini/media/camera_utils.py) | 18-66 | 摄像头自动检测 |
| [camera_constants.py](src/reachy_mini/media/camera_constants.py) | 11-174 | 摄像头常量定义 |
| [media_manager.py](src/reachy_mini/media/media_manager.py) | 30-294 | 媒体管理器 |
| [zenoh_server.py](src/reachy_mini/io/zenoh_server.py) | 40-84 | Zenoh 服务器配置 |
| [zenoh_client.py](src/reachy_mini/io/zenoh_client.py) | 36-57 | Zenoh 客户端配置 |
| [main.py](src/reachy_mini/daemon/app/main.py) | 331-557 | 服务器启动入口 |
| [reachy_mini.py](src/reachy_mini/reachy_mini.py) | 56-900 | ReachyMini SDK 主类 |

### B. 常见问题 (FAQ)

**Q: 如何指定连接到特定 IP 的机器人？**

A: 当前 SDK 使用网络发现，不支持直接指定 IP。确保两台设备在同一局域网，使用 `connection_mode="network"` 即可自动发现。

**Q: 摄像头未检测到怎么办？**

A: 检查 USB 连接，运行 `ls /dev/video*` 确认设备存在，或手动指定串口：`--serialport /dev/video0`。

**Q: 无线版和 Lite 版有什么区别？**

A: 无线版支持 WebRTC 远程流、IMU 传感器，通过 Unix socket 本地传输；Lite 版直接使用 OpenCV 访问本地摄像头。

**Q: 如何更改相机内参？**

A: 相机内参是预标定的，如需重新标定，可修改 [camera_constants.py](src/reachy_mini/media/camera_constants.py) 中的 K 和 D 矩阵。

---

**文档版本**: 1.0
**最后更新**: 2025-01-08
**适用 SDK 版本**: reachy_mini >= 1.2.0
