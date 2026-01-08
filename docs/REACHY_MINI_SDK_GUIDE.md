# Reachy Mini SDK Complete User Guide

## Table of Contents

1. [Camera System Deep Dive](#1-camera-system-deep-dive)
2. [Remote Connection Configuration](#2-remote-connection-configuration)
3. [Server Startup Parameters Explained](#3-server-startup-parameters-explained)
4. [Complete Code Examples](#4-complete-code-examples)

---

## 1. Camera System Deep Dive

### 1.1 Core File Structure

```
src/reachy_mini/media/
├── camera_base.py          # Camera abstract base class
├── camera_opencv.py        # OpenCV backend implementation
├── camera_gstreamer.py     # GStreamer backend implementation
├── camera_constants.py     # Camera constants and specifications
├── camera_utils.py         # Camera auto-detection utilities
└── media_manager.py        # Media manager (unified interface)
```

### 1.2 Supported Camera Hardware

| Camera Type | VID | PID | Resolution Support |
|-------------|-----|-----|-------------------|
| **Reachy Mini Lite** | 0x38FB | 0x1002 | 1920x1080@60fps, 3840x2592@30fps |
| **Arducam 12MP** | 0x0C45 | 0x636D | 2304x1296@30fps, 4608x2592@10fps |
| **Legacy Raspberry Pi Camera** | 0x1BCF | 0x28C4 | Same as Lite version |
| **Reachy Mini Wireless** | - | - | 1920x1080@30fps (via WebRTC) |
| **Generic USB Camera** | - | - | 1280x720@30fps (fallback option) |

### 1.3 Camera Auto-Detection Logic

The `find_camera()` function in [camera_utils.py](src/reachy_mini/media/camera_utils.py#L18-L66) detects cameras in priority order:

```python
1. Reachy Mini Lite camera (VID: 0x38FB, PID: 0x1002)
2. Legacy Raspberry Pi Camera (VID: 0x1BCF, PID: 0x28C4)
3. Arducam 12MP (VID: 0x0C45, PID: 0x636D)
4. Generic camera (fallback to /dev/video0)
```

### 1.4 Camera Backend Comparison

| Feature | OpenCV | GStreamer | WebRTC |
|---------|--------|-----------|--------|
| **Use Case** | Local Lite version | Linux Wireless (local) | Remote client |
| **Hardware Acceleration** | None | VAAPI/NVJPEG | Browser-dependent |
| **Latency** | Medium | Low | Medium |
| **Cross-platform** | Yes | Linux only | Yes |
| **Resolution Setting** | Runtime | Runtime | Fixed |
| **Unix Socket Support** | No | Yes | No |

### 1.5 Resolution Options

All resolutions defined in [camera_constants.py](src/reachy_mini/media/camera_constants.py#L11-L36):

```python
class CameraResolution(Enum):
    R1280x720at30fps   # 720p HD
    R1280x720at60fps   # 720p 60fps
    R1536x864at40fps   # Medium resolution
    R1600x1200at30fps  # 4:3 ratio
    R1920x1080at30fps  # 1080p HD
    R1920x1080at60fps  # 1080p 60fps
    R2304x1296at30fps  # Arducam high resolution
    R3072x1728at10fps  # High pixel count
    R3264x2448at30fps  # 8MP @ 30fps
    R3264x2448at10fps  # 8MP @ 10fps
    R3840x2160at30fps  # 4K UHD
    R3840x2160at10fps  # 4K @ 10fps
    R3840x2592at30fps  # 10MP @ 30fps
    R3840x2592at10fps  # 10MP @ 10fps
    R4608x2592at10fps  # Arducam max resolution
```

### 1.6 Camera Intrinsic Parameters and Distortion Coefficients

Each camera comes pre-calibrated with camera intrinsic matrix **K** and distortion coefficients **D**:

```python
# Reachy Mini Lite camera parameters
K = [[821.515, 0.0,    962.241],
     [0.0,    820.830, 542.459],
     [0.0,    0.0,    1.0]]

D = [-2.944e-02, 6.005e-02, 3.578e-06, -2.965e-04, -3.792e-02]
```

The intrinsic matrix is automatically scaled proportionally when resolution changes.

### 1.7 Basic Camera Usage

```python
from reachy_mini import ReachyMini

# Create instance, SDK automatically detects and initializes camera
with ReachyMini() as reachy:
    # Get a frame (BGR format, numpy array)
    frame = reachy.media.get_frame()

    if frame is not None:
        print(f"Frame shape: {frame.shape}")  # (height, width, 3)
        print(f"Frame dtype: {frame.dtype}")   # uint8

        # Save image
        import cv2
        cv2.imwrite("capture.jpg", frame)

        # Get camera parameters
        camera = reachy.media.camera
        print(f"Resolution: {camera.resolution}")      # (width, height)
        print(f"Framerate: {camera.framerate}")        # fps
        print(f"Camera Matrix K:\n{camera.K}")
        print(f"Distortion D:\n{camera.D}")
```

### 1.8 Setting Camera Resolution

```python
from reachy_mini import ReachyMini
from reachy_mini.media.camera_constants import CameraResolution

with ReachyMini() as reachy:
    # Set resolution to 1080p@30fps
    reachy.media.camera.set_resolution(CameraResolution.R1920x1080at30fps)

    # Or set to 720p@60fps
    reachy.media.camera.set_resolution(CameraResolution.R1280x720at60fps)
```

### 1.9 Media Backend Selection

```python
from reachy_mini import ReachyMini

# Different media backend configurations
backends = {
    # OpenCV + SoundDevice (Lite default)
    "default": "Local OpenCV camera + SoundDevice audio",

    # GStreamer (Linux Wireless version local)
    "gstreamer": "GStreamer camera + audio",

    # WebRTC (Wireless version remote client)
    "webrtc": "Stream via WebRTC",

    # Disable media
    "no_media": "No camera or audio at all"
}

with ReachyMini(media_backend="default") as reachy:
    frame = reachy.media.get_frame()
```

### 1.10 Audio Features

```python
from reachy_mini import ReachyMini

with ReachyMini() as reachy:
    # Play sound
    reachy.media.play_sound("wake_up.wav")

    # Start recording
    reachy.media.start_recording()

    # Get audio sample
    audio_sample = reachy.media.get_audio_sample()

    # Stop recording
    reachy.media.stop_recording()

    # Get sound direction (Direction of Arrival)
    doa = reachy.media.get_DoA()
    if doa is not None:
        angle, speech_detected = doa
        print(f"Sound angle: {angle:.2f} rad, Speech: {speech_detected}")
```

---

## 2. Remote Connection Configuration

### 2.1 Network Architecture Overview

Reachy Mini uses the **Zenoh** protocol for robot control communication:

```
┌─────────────────┐          ┌─────────────────┐
│   PC Client     │          │  Reachy Mini    │
│                 │          │   Server Side   │
│                 │          │                 │
│  ZenohClient    │◄────────►│  ZenohServer    │
│  (peer mode)    │  7447    │  (router mode)  │
│                 │          │                 │
└─────────────────┘          └─────────────────┘
       IP: Any                    IP: 10.42.0.75
```

### 2.2 Connection Modes

| Mode | Description | Zenoh Config | Use Case |
|------|-------------|--------------|----------|
| **auto** | Prefer local, fallback to network discovery | First client then peer | Development & debugging |
| **localhost_only** | Connect to local server only | mode: client | Local development |
| **network** | Network discovery mode | mode: peer + scouting | LAN control |

### 2.3 Zenoh Configuration Details

#### Server Side ([zenoh_server.py](src/reachy_mini/io/zenoh_server.py#L40-L84))

```python
# localhost_only = True (default)
{
    "listen": {"endpoints": ["tcp/localhost:7447"]},
    "scouting": {
        "multicast": {"enabled": False},
        "gossip": {"enabled": False}
    }
}

# localhost_only = False (--no-localhost-only)
{
    "listen": {"endpoints": ["tcp/0.0.0.0:7447"]},  # All interfaces
    "scouting": {
        "multicast": {"enabled": True},   # Multicast discovery
        "gossip": {"enabled": True}       # Gossip between nodes
    },
    "connect": {"endpoints": []}          # Accept any connection
}
```

#### Client Side ([zenoh_client.py](src/reachy_mini/io/zenoh_client.py#L36-L57))

```python
# localhost_only = True
{
    "mode": "client",
    "connect": {"endpoints": ["tcp/localhost:7447"]}
}

# localhost_only = False (network mode)
{
    "mode": "peer",                       # Peer mode
    "scouting": {
        "multicast": {"enabled": True},   # Auto discovery
        "gossip": {"enabled": True}
    },
    "connect": {"endpoints": []}          # Don't force server specification
}
```

### 2.4 Remote Connection Complete Workflow

#### Step 1: Server Startup (Reachy Mini Device)

```bash
# Run on Reachy Mini device (IP: 10.42.0.75)
python -m reachy_mini.daemon.app.main \
    --wireless-version \
    --no-localhost-only \
    --fastapi-host 0.0.0.0 \
    --fastapi-port 8000
```

**Key Parameter Notes:**
- `--wireless-version`: Enable wireless version features
- `--no-localhost-only`: **Core parameter** to allow LAN access
- `--fastapi-host 0.0.0.0`: Web API listens on all interfaces

#### Step 2: Configure Firewall

```bash
# Run on Reachy Mini device
sudo ufw allow 7447/tcp  # Zenoh control port
sudo ufw allow 8000/tcp  # FastAPI Web port
```

#### Step 3: Client Connection (PC)

```python
from reachy_mini import ReachyMini

# Method 1: Using network mode (recommended)
with ReachyMini(
    connection_mode="network",
    timeout=10.0
) as reachy:
    # Control robot
    reachy.goto_target(head={"z": 10}, duration=1.0)

    # Get camera frame
    frame = reachy.media.get_frame()

    # Get joint positions
    head_joints, antenna_joints = reachy.get_current_joint_positions()
    print(f"Head: {head_joints}")
    print(f"Antennas: {antenna_joints}")

# Method 2: Using auto mode (auto fallback)
with ReachyMini(
    connection_mode="auto",  # Try local first, fallback to network
    timeout=10.0
) as reachy:
    # Same as above
    pass
```

### 2.5 Network Discovery Mechanism

Zenoh uses the following mechanisms for automatic device discovery:

1. **Multicast**: Broadcast discovery messages on the LAN
2. **Gossip**: Information propagation between nodes
3. **Peer Mode**: Client and server connect as equals

**Important Notes:**
- Ensure both devices are on the same network segment
- Network must support multicast (enterprise networks may disable it)
- `robot_name` (default `reachy_mini`) is used as Zenoh topic namespace

### 2.6 Port Usage Summary

| Port | Protocol | Purpose | Server Side | Client Side |
|------|----------|---------|-------------|-------------|
| **7447** | TCP | Zenoh robot control | Listen | Connect |
| **8000** | HTTP | FastAPI Web API | Listen | Access |
| **8443** | TCP | WebRTC signaling (Wireless) | Listen | Connect |

### 2.7 Troubleshooting

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Connection timeout | Firewall blocking | Open ports 7447, 8000 |
| Cannot discover device | Not on same network segment | Check IP configuration |
| Media stream failure | Backend mismatch | Check `media_backend` setting |
| Multicast failure | Network disables multicast | Use switch or configure router |

---

## 3. Server Startup Parameters Explained

### 3.1 Startup Command Template

```bash
python -m reachy_mini.daemon.app.main [options]
```

### 3.2 Complete Parameter List

#### Version Control Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--wireless-version` | flag | `False` | Enable wireless version mode (additional routing) |
| `--desktop-app-daemon` | flag | `False` | Desktop app daemon mode |

#### Network Configuration Parameters (Remote Control Key)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--localhost-only` | flag | `True` (Wireless `False`) | **Restrict to local access only** |
| `--no-localhost-only` | flag | - | **Allow LAN access** |
| `--fastapi-host` | string | `0.0.0.0` | FastAPI listen address |
| `--fastapi-port` | int | `8000` | FastAPI port |
| `--robot-name` | string | `reachy_mini` | Robot name (Zenoh prefix) |

#### Robot Control Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-p, --serialport` | string | `auto` | Serial port (auto-detect or manual like `/dev/ttyACM0`) |
| `--hardware-config-filepath` | string | Built-in path | Hardware config YAML file path |
| `--wake-up-on-start` | flag | `True` | Auto wake robot on startup |
| `--no-wake-up-on-start` | flag | - | Don't wake on startup |
| `--goto-sleep-on-stop` | flag | `True` | Auto sleep on stop |
| `--no-goto-sleep-on-stop` | flag | - | Don't sleep on stop |

#### Simulation Mode Parameters

| Parameter | Description |
|-----------|-------------|
| `--sim` | Use MuJoCo simulation mode |
| `--mockup-sim` | Lightweight simulation (no MuJoCo needed) |
| `--scene` | Simulation scene name (default: `empty`) |
| `--headless` | MuJoCo no GUI mode |

#### Kinematics Parameters

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `--kinematics-engine` | string | `AnalyticalKinematics` | `Placo`, `NN`, `AnalyticalKinematics` |
| `--check-collision` | flag | `False` | Enable collision detection |

#### Media & WebSocket Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--websocket-uri` | string | `None` | WebSocket URI (e.g., `ws://localhost:8000`) |
| `--stream-media` | flag | `False` | Stream media via WebSocket |
| `--deactivate-audio` | flag | - | Disable audio (enabled by default) |

#### Daemon Control Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--autostart` | flag | `True` | Auto start daemon |
| `--no-autostart` | flag | - | Don't auto start |
| `--timeout-health-check` | float | `None` | Health check timeout (seconds) |

#### Logging Parameters

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `--log-level` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `--log-file` | string | `None` | Log file path |

### 3.3 Common Startup Configuration Examples

#### Configuration 1: Local Development (Lite Version)

```bash
python -m reachy_mini.daemon.app.main \
    --log-level DEBUG \
    --autostart
```

#### Configuration 2: LAN Remote Control

```bash
python -m reachy_mini.daemon.app.main \
    --wireless-version \
    --no-localhost-only \
    --fastapi-host 0.0.0.0 \
    --fastapi-port 8000
```

#### Configuration 3: Simulation Mode

```bash
python -m reachy_mini.daemon.app.main \
    --sim \
    --scene minimal \
    --headless
```

#### Configuration 4: Production Environment (Full Configuration)

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

### 3.4 Wireless Version Additional Features

When using `--wireless-version`, the following routes are additionally enabled:

| Route | Function |
|-------|----------|
| `/cache` | Cache management |
| `/update` | System update |
| `/wifi_config` | WiFi configuration |
| `/logs` | Log viewing |

### 3.5 Server Status Check

After successful startup, you can access:

- **Dashboard**: `http://10.42.0.75:8000/`
- **Settings** (Wireless): `http://10.42.0.75:8000/settings`
- **Logs** (Wireless): `http://10.42.0.75:8000/logs`

---

## 4. Complete Code Examples

### 4.1 Basic Remote Control Example

```python
"""
Reachy Mini Remote Control Complete Example
Demonstrates: Connection, movement, getting camera frames, getting sensor data
"""

from reachy_mini import ReachyMini
import numpy as np
import cv2

def main():
    # Connect to Reachy Mini on LAN
    # Server side must be started with: --no-localhost-only
    with ReachyMini(
        connection_mode="network",  # Use network discovery mode
        timeout=10.0,               # Connection timeout 10 seconds
        media_backend="default"     # Use default media backend
    ) as reachy:

        print("✅ Connected to Reachy Mini")

        # ===== 1. Get Camera Frame =====
        frame = reachy.media.get_frame()
        if frame is not None:
            print(f"📷 Camera resolution: {frame.shape}")

            # Save first frame
            cv2.imwrite("reachy_camera.jpg", frame)
            print("💾 Saved image to reachy_camera.jpg")

        # ===== 2. Move Robot Head =====
        print("🎯 Moving to initial position...")
        reachy.goto_target(
            head=np.eye(4),           # Identity matrix = initial position
            antennas=[0.0, 0.0],      # Zero antennas
            duration=2.0
        )

        # ===== 3. Look Up 20 Degrees =====
        print("👆 Looking up...")
        import time
        time.sleep(0.5)

        from scipy.spatial.transform import Rotation as R
        pose_up = np.eye(4)
        pose_up[:3, :3] = R.from_euler('xyz', [20, 0, 0], degrees=True).as_matrix()
        reachy.goto_target(head=pose_up, duration=1.0)

        # ===== 4. Get Joint Positions =====
        head_joints, antenna_joints = reachy.get_current_joint_positions()
        print(f"🦾 Head joints: {head_joints}")
        print(f"📡 Antenna angles: {antenna_joints}")

        # ===== 5. Get Current Head Pose =====
        head_pose = reachy.get_current_head_pose()
        print(f"📍 Head pose matrix:\n{head_pose}")

        # ===== 6. Check IMU Data (Wireless version only) =====
        if reachy.imu is not None:
            print("🧭 IMU data available:")
            print(f"   Accelerometer: {reachy.imu['accelerometer']}")
            print(f"   Gyroscope: {reachy.imu['gyroscope']}")
            print(f"   Quaternion: {reachy.imu['quaternion']}")
        else:
            print("⚠️  IMU not available (Lite version)")

        # ===== 7. Play Sound =====
        print("🔊 Playing wake-up sound...")
        reachy.media.play_sound("wake_up.wav")

        # ===== 8. Use look_at Feature =====
        # Look at specific point in image
        print("👀 Looking at image center...")
        if reachy.media.camera is not None:
            width, height = reachy.media.camera.resolution
            reachy.look_at_image(
                u=width // 2,    # Horizontal center
                v=height // 2,   # Vertical center
                duration=1.0
            )

        # ===== 9. Look at Point in 3D Space =====
        print("🎯 Looking at 0.5m in front...")
        reachy.look_at_world(
            x=0.5,  # X: forward
            y=0.0,  # Y: left
            z=0.0,  # Z: up
            duration=1.0
        )

        print("✨ Demo complete!")

if __name__ == "__main__":
    main()
```

### 4.2 Camera Advanced Usage Example

```python
"""
Camera Advanced Features Example
Demonstrates: Resolution settings, camera parameters usage, image processing
"""

from reachy_mini import ReachyMini
from reachy_mini.media.camera_constants import CameraResolution
import cv2
import numpy as np

def camera_advanced_demo():
    with ReachyMini() as reachy:
        camera = reachy.media.camera

        if camera is None:
            print("❌ Camera not initialized")
            return

        # ===== 1. View Available Resolutions =====
        specs = camera.camera_specs
        print(f"📷 Camera model: {specs.name}")
        print(f"Available resolutions:")
        for res in specs.available_resolutions:
            print(f"  - {res.name}")

        # ===== 2. Switch Resolution =====
        print("\n🔄 Switching to 720p@60fps...")
        camera.set_resolution(CameraResolution.R1280x720at60fps)
        print(f"Current resolution: {camera.resolution}")
        print(f"Current framerate: {camera.framerate} fps")

        # ===== 3. Get Camera Intrinsics =====
        K = camera.K
        D = camera.D
        print(f"\n📐 Camera intrinsic matrix K:\n{K}")
        print(f"🔧 Distortion coefficients D: {D}")

        # ===== 4. Distortion Correction Example =====
        frame = reachy.media.get_frame()
        if frame is not None:
            h, w = frame.shape[:2]

            # Distortion correction
            newcameramtx, roi = cv2.getOptimalNewCameraMatrix(
                K, D, (w, h), 1, (w, h)
            )
            undistorted = cv2.undistort(frame, K, D, None, newcameramtx)

            # Save comparison image
            comparison = np.hstack([frame, undistorted])
            cv2.imwrite("distortion_comparison.jpg", comparison)
            print("💾 Saved distortion comparison image")

        # ===== 5. Real-time Capture =====
        print("\n📹 Real-time capturing 10 frames...")
        for i in range(10):
            frame = reachy.media.get_frame()
            if frame is not None:
                print(f"Frame {i+1}: {frame.shape}, dtype={frame.dtype}")

        # ===== 6. Resolution Performance Test =====
        resolutions = [
            CameraResolution.R1280x720at30fps,
            CameraResolution.R1920x1080at30fps,
        ]

        print("\n⚡ Resolution performance test:")
        for res in resolutions:
            camera.set_resolution(res)
            import time

            # Measure time to get 10 frames
            start = time.time()
            for _ in range(10):
                reachy.media.get_frame()
            elapsed = time.time() - start

            fps = 10 / elapsed
            print(f"  {res.name}: Actual {fps:.1f} fps")

if __name__ == "__main__":
    camera_advanced_demo()
```

### 4.3 Recording and Playback Example

```python
"""
Recording and Playback Robot Movements Example
"""

from reachy_mini import ReachyMini
import numpy as np
import time

def recording_demo():
    with ReachyMini(connection_mode="network") as reachy:

        # ===== 1. Record Movements =====
        print("🔴 Starting recording (5 seconds)...")
        reachy.start_recording()

        start_time = time.time()
        while time.time() - start_time < 5.0:
            # Perform some movements
            pose = np.eye(4)
            pose[0, 3] = 0.1 * np.sin(time.time() * 2)  # Left-right movement
            reachy.set_target(head=pose)
            time.sleep(0.1)

        recorded_data = reachy.stop_recording()
        print(f"✅ Recording complete, {len(recorded_data)} frames")

        # ===== 2. View Recorded Data =====
        print("\n📊 Recorded data sample:")
        for i, frame in enumerate(recorded_data[:3]):
            print(f"Frame {i}:")
            print(f"  Time: {frame['time']:.2f}")
            if 'head' in frame:
                print(f"  Head pose: {frame['head'][:3][:3]}")  # Partial matrix
            if 'antennas' in frame:
                print(f"  Antennas: {frame['antennas']}")

        # ===== 3. Playback Movements =====
        print("\n▶️  Playing back movements...")

        # Return to starting position
        first_frame = recorded_data[0]
        if 'head' in first_frame:
            start_pose = np.array(first_frame['head'])
            reachy.goto_target(head=start_pose, duration=1.0)

        time.sleep(1)

        # Frame-by-frame playback
        for frame in recorded_data:
            if 'head' in frame:
                pose = np.array(frame['head'])
                reachy.set_target(head=pose)
            if 'antennas' in frame:
                antennas = frame['antennas']
                reachy.set_target(antennas=antennas)

            # Control playback speed based on recorded timing
            time.sleep(0.05)  # 20fps playback

        print("✅ Playback complete")

if __name__ == "__main__":
    recording_demo()
```

---

## Appendix

### A. File References

| File | Lines | Description |
|------|-------|-------------|
| [camera_base.py](src/reachy_mini/media/camera_base.py) | 21-101 | Camera abstract base class |
| [camera_opencv.py](src/reachy_mini/media/camera_opencv.py) | 22-90 | OpenCV camera implementation |
| [camera_gstreamer.py](src/reachy_mini/media/camera_gstreamer.py) | 40-200+ | GStreamer camera implementation |
| [camera_utils.py](src/reachy_mini/media/camera_utils.py) | 18-66 | Camera auto-detection |
| [camera_constants.py](src/reachy_mini/media/camera_constants.py) | 11-174 | Camera constants definition |
| [media_manager.py](src/reachy_mini/media/media_manager.py) | 30-294 | Media manager |
| [zenoh_server.py](src/reachy_mini/io/zenoh_server.py) | 40-84 | Zenoh server configuration |
| [zenoh_client.py](src/reachy_mini/io/zenoh_client.py) | 36-57 | Zenoh client configuration |
| [main.py](src/reachy_mini/daemon/app/main.py) | 331-557 | Server startup entry |
| [reachy_mini.py](src/reachy_mini/reachy_mini.py) | 56-900 | ReachyMini SDK main class |

### B. Frequently Asked Questions (FAQ)

**Q: How do I specify connection to a robot at a specific IP?**

A: The current SDK uses network discovery and doesn't support direct IP specification. Ensure both devices are on the same LAN and use `connection_mode="network"` for automatic discovery.

**Q: What if the camera is not detected?**

A: Check USB connection, run `ls /dev/video*` to confirm device exists, or manually specify port: `--serialport /dev/video0`.

**Q: What's the difference between Wireless and Lite versions?**

A: Wireless version supports WebRTC remote streaming, IMU sensors, and local transmission via Unix socket; Lite version directly uses OpenCV to access local camera.

**Q: How do I change camera intrinsic parameters?**

A: Camera intrinsics are pre-calibrated. To recalibrate, modify the K and D matrices in [camera_constants.py](src/reachy_mini/media/camera_constants.py).

---

**Document Version**: 1.0
**Last Updated**: 2025-01-08
**Applicable SDK Version**: reachy_mini >= 1.2.0