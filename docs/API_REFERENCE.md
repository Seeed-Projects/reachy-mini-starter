# Reachy Mini API Reference Guide

Complete Reachy Mini robot control interface documentation, covering all parameter ranges, controllable degrees of freedom, and usage limitations.

---

## Table of Contents

1. [REST API Interface](#1-rest-api-interface)
2. [WebSocket Interface](#2-websocket-interface)
3. [Zenoh Protocol Interface](#3-zenoh-protocol-interface)
4. [BLE Bluetooth Interface](#4-ble-bluetooth-interface)
5. [Appendix](#5-appendix)

---

## 1. REST API Interface

**Base URL**: `http://192.168.137.225:8000`

**Features**: HTTP-based request-response mode, suitable for single commands and configuration queries, latency 20-50ms

### 1.1 Motion Control `/move`

#### Controllable Objects and Parameter Ranges

| Object | Parameter | Range | Unit | Description |
|---------|-----------|-------|------|-------------|
| **Head Pose** | x | ±0.05 | m | Front-back position, forward is positive |
| | y | ±0.05 | m | Left-right position, left is positive |
| | z | -0.03 ~ +0.08 | m | Up-down position, up is positive |
| | roll | ±25 | deg | Roll angle, right tilt is positive |
| | pitch | ±35 | deg | Pitch angle, head up is positive |
| | yaw | ±160 | deg | Yaw angle, left turn is positive |
| **Antennas** | antennas[0] | -80 ~ +80 | deg | Left antenna angle |
| | antennas[1] | -80 ~ +80 | deg | Right antenna angle |
| **Body** | body_yaw | -160 ~ +160 | deg | Body yaw angle |
| **Motion Params** | duration | 0.1 ~ 10.0 | s | Motion duration |

**Interpolation Methods**:
| Method | Description |
|--------|-------------|
| `linear` | Linear interpolation, constant velocity motion |
| `minjerk` | Minimum jerk interpolation, smooth motion (recommended) |
| `ease` | Ease interpolation, smooth acceleration/deceleration |
| `cartoon` | Cartoon interpolation, elastic effect |

#### Interface List

**POST `/move/goto`** - Smooth motion to target (with interpolation)

Request example:
```json
{
  "head_pose": {"x": 0, "y": 0, "z": 0.05, "roll": 0, "pitch": 15, "yaw": 0},
  "antennas": [30, -30],
  "body_yaw": 0,
  "duration": 2.0,
  "interpolation": "minjerk"
}
```

Response:
```json
{"uuid": "123e4567-e89b-12d3-a456-426614174000"}
```

---

**POST `/move/set_target`** - Set target immediately (no trajectory)

Request example:
```json
{
  "target_head_pose": {
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
  },
  "target_antennas": [0.0, 0.0],
  "target_body_yaw": 0.0
}
```

---

**POST `/move/goto_joint_positions`** - Joint space motion

| Object | Parameter | Range | Unit | Description |
|---------|-----------|-------|------|-------------|
| **Head Joints** | head_joint_positions[0] | ±2.79 | rad | yaw_body (-160°~+160°) |
| | head_joint_positions[1] | -0.84 ~ +1.40 | rad | roll_sp_1 (-48°~+80°) |
| | head_joint_positions[2] | -0.84 ~ +1.40 | rad | roll_sp_2 (-48°~+80°) |
| | head_joint_positions[3] | -0.84 ~ +1.40 | rad | roll_sp_3 (-48°~+80°) |
| | head_joint_positions[4] | -1.22 ~ +1.40 | rad | pitch_sp_1 (-70°~+80°) |
| | head_joint_positions[5] | -0.84 ~ +1.40 | rad | pitch_sp_2 (-48°~+80°) |
| | head_joint_positions[6] | -1.22 ~ +1.40 | rad | pitch_sp_3 (-70°~+80°) |
| **Antenna Joints** | antennas_joint_positions[0] | ±1.40 | rad | Left antenna (-80°~+80°) |
| | antennas_joint_positions[1] | ±1.40 | rad | Right antenna (-80°~+80°) |

---

**POST `/move/play/wake_up`** - Wake up animation

**POST `/move/play/goto_sleep`** - Go to sleep animation

**POST `/move/play/recorded-move-dataset/{dataset}/{move}`** - Play preset motion
- Example: `/move/play/recorded-move-dataset/pollen-robotics/reachy-mini-dances-library/another_one_bites_the_dust`

**GET `/move/running`** - Get running motions

**POST `/move/stop`** - Stop motion

---

### 1.2 State Query `/state`

#### Queryable Objects

| Object | Interface | Return Data | Value Range |
|---------|-----------|-------------|-------------|
| **Head Pose** | GET `/state/present_head_pose` | x, y, z, roll, pitch, yaw | See section 1.1 |
| **Body Yaw** | GET `/state/present_body_yaw` | Radian value | -2.79 ~ +2.79 |
| **Antenna Position** | GET `/state/present_antenna_joint_positions` | [Left, Right] radians | ±1.40 |
| **Full State** | GET `/state/full` | All states | - |

**GET `/state/full` Query Parameters**:
| Parameter | Default | Description |
|-----------|---------|-------------|
| with_control_mode | true | Control mode |
| with_head_pose | true | Current head pose |
| with_target_head_pose | false | Target head pose |
| with_head_joints | false | Head joint angles |
| with_target_head_joints | false | Target joint angles |
| with_body_yaw | true | Body yaw |
| with_target_body_yaw | false | Target body yaw |
| with_antenna_positions | true | Antenna positions |
| with_target_antenna_positions | false | Target antenna positions |
| with_passive_joints | false | Passive joints |
| use_pose_matrix | false | Use matrix format |

---

### 1.3 Motor Control `/motors`

#### Controllable Objects

| Control Object | Parameter | Description |
|----------------|-----------|-------------|
| **Motor Mode** | `enabled` | Motor enabled, rigid control (mode 3) |
| | `disabled` | Motor disabled, manual movement allowed (mode 0) |
| | `gravity_compensation` | Gravity compensation, maintain pose (mode 5) |

**Interface List**:
- **GET `/motors/status`** - Get motor status
- **POST `/motors/set_mode/{mode}`** - Set motor mode

---

### 1.4 Audio Control `/volume`

#### Controllable Objects and Parameter Ranges

| Object | Parameter | Range | Default | Unit |
|---------|-----------|-------|---------|------|
| **Volume** | volume | 0 ~ 100 | 50 | % |
| **Mic Volume** | volume | 0 ~ 100 | 50 | % |
| **Sample Rate** | sample_rate | 16000 | - | Hz |
| **Channels** | channels | 2 | - | - |
| **Sound Direction** | doa_angle | 0 ~ π | - | rad |

**Sound Direction Guide**:
| Radian | Direction |
|--------|-----------|
| 0 | Left |
| π/2 | Front/Back |
| π | Right |

#### Interface List

**GET `/volume/current`** - Get speaker volume

Response:
```json
{"volume": 50, "device": "reachy_mini_audio", "platform": "Linux"}
```

**POST `/volume/set`** - Set speaker volume

Request:
```json
{"volume": 75}
```

Response:
```json
{"volume": 75, "device": "reachy_mini_audio", "platform": "Linux"}
```

**POST `/volume/test-sound`** - Play test sound

Response:
```json
{"status": "ok", "message": "Test sound played"}
```

**GET `/volume/microphone/current`** - Get microphone gain

Response:
```json
{"volume": 60, "device": "reachy_mini_audio", "platform": "Linux"}
```

**POST `/volume/microphone/set`** - Set microphone gain

Request:
```json
{"volume": 80}
```

---

### 1.5 Application Management `/apps`

| Interface | Method | Description |
|-----------|--------|-------------|
| `/apps/list-available` | GET | List available apps |
| `/apps/install` | POST | Install app |
| `/apps/start-app/{app_name}` | POST | Start app |
| `/apps/stop-current-app` | POST | Stop app |
| `/apps/current-app-status` | GET | Get app status |

**Install app request example**:
```json
{"source": "huggingface", "app_id": "pollen-robotics/reachy_mini_conversation_app"}
```

---

### 1.6 Kinematics `/kinematics`

| Engine Type | Description |
|-------------|-------------|
| `AnalyticalKinematics` | Analytical solution (default, fastest) |
| `PlacoKinematics` | Optimization solution (with collision detection) |
| `NNKinematics` | Neural network (requires model) |

| Interface | Method | Description |
|-----------|--------|-------------|
| `/kinematics/info` | GET | Get kinematics info |
| `/kinematics/urdf` | GET | Get URDF model |
| `/kinematics/stl/{filename}` | GET | Get STL file (3D visualization) |

---

### 1.7 Daemon `/daemon`

| Interface | Method | Description |
|-----------|--------|-------------|
| `/daemon/start` | POST | Start daemon |
| `/daemon/stop` | POST | Stop daemon |
| `/daemon/restart` | POST | Restart daemon |
| `/daemon/status` | GET | Get status |

---

## 2. WebSocket Interface

**Features**: Bidirectional real-time communication, latency <10ms, supports 60Hz+ high-frequency control

### 2.1 Real-time Control `/move/ws/set_target`

**Connection**: `ws://192.168.137.225:8000/move/ws/set_target`

#### Controllable Objects and Parameter Ranges

| Object | Parameter | Range | Unit | Description |
|---------|-----------|-------|------|-------------|
| **Head Pose** | position.x | ±0.05 | m | Front-back position |
| | position.y | ±0.05 | m | Left-right position |
| | position.z | -0.03 ~ +0.08 | m | Up-down position |
| | rotation (quaternion) | Unit quaternion | - | Orientation |
| **Antennas** | target_antennas[0] | -80 ~ +80 | deg | Left antenna |
| | target_antennas[1] | -80 ~ +80 | deg | Right antenna |
| **Body** | target_body_yaw | -160 ~ +160 | deg | Body yaw |

**Send message format** (60Hz+):
```json
{
  "target_head_pose": {
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
  },
  "target_antennas": [0.0, 0.0],
  "target_body_yaw": 0.0
}
```

**Receive error feedback**:
```json
{"status": "error", "detail": "error message"}
```

---

### 2.2 State Stream `/state/ws/full`

**Connection**: `ws://192.168.137.225:8000/state/ws/full?frequency=30`

#### Query Parameters and Controllable Range

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| frequency | 1 ~ 100 | 10 | Update frequency (Hz) |
| with_head_pose | true/false | true | Include head pose |
| with_head_joints | true/false | false | Include joint angles |
| with_antenna_positions | true/false | true | Include antenna positions |
| use_pose_matrix | true/false | false | Use matrix format |

**Receive message** (continuous stream):
```json
{
  "control_mode": "enabled",
  "head_pose": {"x": 0.0, "y": 0.0, "z": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0},
  "body_yaw": 0.0,
  "antennas_position": [0.0, 0.0],
  "timestamp": "2025-12-26T10:00:00Z"
}
```

---

### 2.3 Motion Updates `/move/ws/updates`

**Connection**: `ws://192.168.137.225:8000/move/ws/updates`

#### Event Types

| Event Type | Description |
|------------|-------------|
| `move_started` | Motion started |
| `move_completed` | Motion completed |
| `move_failed` | Motion failed |
| `move_cancelled` | Motion cancelled |

**Receive event**:
```json
{
  "type": "move_started",
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "details": ""
}
```

---

## 3. Zenoh Protocol Interface

**Features**: SDK main communication method, latency 10-20ms, high bandwidth, supports high-frequency control

### 3.1 Connection Configuration

**Client mode (specify IP)**:
```python
{"mode": "client", "connect": {"endpoints": ["tcp/192.168.137.225:7447"]}}
```

**Peer mode (auto-discovery)**:
```python
{"mode": "peer", "scouting": {"multicast": {"enabled": true}}}
```

---

### 3.2 Topics and Controllable Objects

| Topic | Direction | Controllable/Return Objects | Data Type |
|-------|-----------|----------------------------|-----------|
| `reachy_mini/command` | → | Head pose, antennas, body yaw, motor mode | dict |
| `reachy_mini/joint_positions` | ← | All 9 joint positions | list |
| `reachy_mini/head_pose` | ← | Head 4x4 pose matrix | ndarray |
| `reachy_mini/daemon_status` | ← | Daemon status | dict |
| `reachy_mini/task` | → | Task request | dict |
| `reachy_mini/task_progress` | ← | Task progress | dict |
| `reachy_mini/recorded_data` | ← | Recorded data | bytes |

---

### 3.3 Command Format and Parameter Ranges

#### Send command to `reachy_mini/command`

**Set target pose**:
```python
{
    "head_pose": [[4x4 matrix]],  # Head pose matrix
    "antennas_joint_positions": [0.5, -0.5],  # Antenna radians [-1.40, +1.40]
    "body_yaw": 0.0  # Body yaw radians [-2.79, +2.79]
}
```

**Enable torque**:
```python
{"torque": True}
```

**Enable gravity compensation**:
```python
{"gravity_compensation": True}
```

---

### 3.4 Return Data Format

**Joint positions** (`reachy_mini/joint_positions`):
```python
[
    yaw_body,      # [0] ±2.79 rad (±160°)
    roll_sp_1,     # [1] -0.84~+1.40 rad (-48°~+80°)
    roll_sp_2,     # [2] -0.84~+1.40 rad (-48°~+80°)
    roll_sp_3,     # [3] -0.84~+1.40 rad (-48°~+80°)
    pitch_sp_1,    # [4] -1.22~+1.40 rad (-70°~+80°)
    pitch_sp_2,    # [5] -0.84~+1.40 rad (-48°~+80°)
    pitch_sp_3,    # [6] -1.22~+1.40 rad (-70°~+80°)
    antenna_left,  # [7] ±1.40 rad (±80°)
    antenna_right  # [8] ±1.40 rad (±80°)
]
```

---

## 4. BLE Bluetooth Interface

**Features**: Close-range configuration, debugging, emergency control, latency 100-500ms

### 4.1 Connection Information

| Item | Value |
|-----|-------|
| **BLE Device Name** | ReachyMini |
| **PIN Code** | Last 5 digits of serial number (`dfu-util -l` to query) |

### 4.2 Using nRF Connect to Connect

1. Install nRF Connect (Android/iOS)
2. Scan and connect to "ReachyMini" device
3. Unknown Service → WRITE to send hex commands

### 4.3 Controllable Commands and Parameters

| Command | Hexadecimal | Description |
|---------|-------------|-------------|
| **PIN Verification** | `50494E5F3030303033` | PIN_00033 (replace with actual PIN) |
| **Query Status** | `535441545553` | STATUS |
| **Reset Hotspot** | `434D445F484F5453504F54` | CMD_HOTSPOT |
| **Restart Daemon** | `434D445F524553544152545F4441454D4F4E` | CMD_RESTART_DAEMON |
| **Software Reset** | `434D445F534F4654574152455F5245534554` | CMD_SOFTWARE_RESET |

### 4.4 Web Bluetooth Tool

Official tool: https://pollen-robotics.github.io/reachy_mini/

Supports Chrome-based browsers, can connect via webpage directly.

---

## 5. Appendix

### 5.1 Robot Degrees of Freedom Overview

| Part | DOF Count | Joint Name | Range (deg) | Range (rad) |
|------|-----------|------------|-------------|-------------|
| **Head** | 7 | yaw_body | ±160° | ±2.79 |
| | | roll_sp_1/2/3 | -48° ~ +80° | -0.84 ~ +1.40 |
| | | pitch_sp_1/2/3 | -70° ~ +80° | -1.22 ~ +1.40 |
| **Antennas** | 2 | Left antenna | ±80° | ±1.40 |
| | | Right antenna | ±80° | ±1.40 |
| **Body** | 1 | body_yaw | ±160° | ±2.79 |

**Total**: 10 controllable degrees of freedom

### 5.2 Task Space Workspace

| Axis | Range | Unit | Description |
|------|-------|------|-------------|
| X (front-back) | ±0.05 | m | Forward is positive |
| Y (left-right) | ±0.05 | m | Left is positive |
| Z (up-down) | -0.03 ~ +0.08 | m | Up is positive |
| Roll | ±25 | deg | Right tilt is positive |
| Pitch | ±35 | deg | Head up is positive |
| Yaw | ±160 | deg | Left turn is positive |

### 5.3 Usage Scenario Recommendations

| Scenario | Recommended Interface | Reason |
|----------|---------------------|--------|
| **Real-time Tracking** | WebSocket `/move/ws/set_target` | 60Hz+, low latency |
| **State Monitoring** | WebSocket `/state/ws/full` | Adjustable frequency, complete data |
| **Single Motion** | REST `/move/goto` | Simple and reliable |
| **Python Development** | Zenoh SDK | Official support |
| **Web Application** | REST + WebSocket | Browser compatible |
| **Mobile App** | REST API | Standard HTTP |
| **Configuration/Debug** | BLE | Close-range configuration |

### 5.4 Pose Representation Formats

#### Euler Angle Format (degrees)
```json
{"x": 0.0, "y": 0.0, "z": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}
```

#### Quaternion Format
```json
{"position": {"x": 0.0, "y": 0.0, "z": 0.0}, "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}}
```

#### 4x4 Matrix Format (flattened)
```json
{"m": [r11, r12, r13, x, r21, r22, r23, y, r31, r32, r33, z, 0, 0, 0, 1]}
```

### 5.5 Important Notes

1. **Coordinate System**: Right-handed coordinate system, X axis forward, Z axis up
2. **Angle Units**: API uses degrees, internal uses radians
3. **Safety Limits**: All joints have software/hardware limit protection
4. **Motor Protection**: Avoid staying at limit positions for extended periods
5. **Network Latency**: WebSocket <10ms, REST 20-50ms
6. **Control Frequency**: Recommended not to exceed 60Hz to avoid command congestion
7. **Priority**: goto commands during motion will be ignored (need to stop first)

---

## Example Code

### JavaScript Real-time Control

```javascript
const controlWS = new WebSocket('ws://192.168.137.225:8000/move/ws/set_target');
const stateWS = new WebSocket('ws://192.168.137.225:8000/state/ws/full?frequency=60');

// Real-time control (60Hz)
function setHeadPose(x, y, z, roll, pitch, yaw) {
  const command = {
    target_head_pose: {
      position: { x, y, z },
      rotation: eulerToQuaternion(roll, pitch, yaw)
    }
  };
  controlWS.send(JSON.stringify(command));
}

// State callback
stateWS.onmessage = (event) => {
  const state = JSON.parse(event.data);
  console.log('Head position:', state.head_pose);
};
```

### Python Smooth Motion

```python
import requests

# Smooth motion to target
data = {
    "head_pose": {"x": 0, "y": 0, "z": 0.05, "roll": 0, "pitch": 15, "yaw": 0},
    "antennas": [30, -30],
    "body_yaw": 0,
    "duration": 2.0,
    "interpolation": "minjerk"
}
response = requests.post('http://192.168.137.225:8000/move/goto', json=data)
print(f"Motion UUID: {response.json()['uuid']}")
```

### Python State Query

```python
import requests

response = requests.get('http://192.168.137.225:8000/state/full')
state = response.json()

print(f"Head pose: {state['head_pose']}")
print(f"Antenna positions: {state['antennas_position']}")
print(f"Control mode: {state['control_mode']}")
```

### Python Audio Control (REST API)

```python
import requests

base_url = "http://192.168.137.225:8000"

# Get current volume
response = requests.get(f"{base_url}/volume/current")
print(f"Volume: {response.json()['volume']}%")

# Set volume
requests.post(f"{base_url}/volume/set", json={"volume": 80})

# Play test sound
requests.post(f"{base_url}/volume/test-sound")

# Get microphone gain
response = requests.get(f"{base_url}/volume/microphone/current")
print(f"Microphone gain: {response.json()['volume']}%")

# Set microphone gain
requests.post(f"{base_url}/volume/microphone/set", json={"volume": 70})
```

### Python Audio Control (SDK)

```python
from reachy_mini import ReachyMini

# Initialize robot
robot = ReachyMini()

# ===== Audio Playback =====

# Play audio file
robot.media.play_sound("wake_up.wav")

# Audio stream playback
robot.media.start_playing()
import numpy as np
# Generate or load audio data (float32, -1.0 to 1.0)
audio_data = np.random.uniform(-0.5, 0.5, 16000).astype(np.float32)
robot.media.push_audio_sample(audio_data)
robot.media.stop_playing()

# Get audio output parameters
sample_rate = robot.media.get_output_audio_samplerate()  # 16000 Hz
channels = robot.media.get_output_channels()             # 2 (stereo)

# ===== Audio Recording =====

# Start recording
robot.media.start_recording()

# Get audio sample
audio_sample = robot.media.get_audio_sample()  # Returns numpy array or bytes
if audio_sample is not None:
    print(f"Sampled {len(audio_sample)} audio points")

# Stop recording
robot.media.stop_recording()

# Get audio input parameters
input_sample_rate = robot.media.get_input_audio_samplerate()  # 16000 Hz
input_channels = robot.media.get_input_channels()             # 2 (stereo)

# ===== Sound Source Direction Detection =====

# Get sound direction
doa_result = robot.media.audio.get_DoA()
if doa_result:
    angle_radians, speech_detected = doa_result
    angle_degrees = angle_radians * 180 / 3.14159
    print(f"Sound direction: {angle_degrees:.1f}°")
    print(f"Speech detected: {speech_detected}")

# ===== Low-level Hardware Control =====

from reachy_mini.media.audio_control_utils import init_respeaker_usb

# Initialize ReSpeaker device
respeaker = init_respeaker_usb()

if respeaker:
    # Read microphone gain
    mic_gain = respeaker.read("AUDIO_MGR_MIC_GAIN")
    print(f"Microphone gain: {mic_gain}")

    # Set microphone gain (float value)
    respeaker.write("AUDIO_MGR_MIC_GAIN", [2.5])

    # LED control
    respeaker.write("LED_BRIGHTNESS", [80])           # Brightness 0-100
    respeaker.write("LED_COLOR", [0xFF0000])          # RGB red
    respeaker.write("LED_EFFECT", [1])                # Effect mode

    # Read firmware version
    version = respeaker.read("VERSION")
    print(f"Firmware version: {version}")
```

### Python Recording and Save Example

```python
from reachy_mini import ReachyMini
import numpy as np
import wave

robot = ReachyMini()

# Start recording
robot.media.start_recording()
print("Recording...")

# Record for 5 seconds
import time
sample_rate = robot.media.get_input_audio_samplerate()
duration = 5  # seconds
all_samples = []

start_time = time.time()
while time.time() - start_time < duration:
    sample = robot.media.get_audio_sample()
    if sample is not None:
        all_samples.append(sample)
    time.sleep(0.01)

robot.media.stop_recording()
print("Recording complete")

# Save as WAV file
if all_samples:
    audio_array = np.concatenate(all_samples)

    # Convert to int16 PCM
    audio_int16 = (audio_array * 32767).astype(np.int16)

    with wave.open("recording.wav", "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

    print("Saved as recording.wav")
```

### Python TTS Speech Synthesis Example

```python
from reachy_mini import ReachyMini
import numpy as np

robot = ReachyMini()

# Use pyttsx3 offline TTS (requires: pip install pyttsx3)
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 150)    # Speech rate
engine.setProperty('volume', 0.9)  # Volume

# Save speech to file and play
engine.save_to_file('Hello, I am Reachy Mini!', 'hello.wav')
engine.runAndWait()

# Play
robot.media.play_sound("hello.wav")
```

### Python WebSocket Audio Stream

```python
from reachy_mini.io.audio_ws import AsyncWebSocketAudioStreamer
import numpy as np

# Connect to audio stream server
streamer = AsyncWebSocketAudioStreamer(
    "ws://192.168.137.225:8765/audio",
    keep_alive_interval=2.0
)

# Send audio (supports bytes, int16 or float32)
audio_chunk = np.random.uniform(-0.3, 0.3, 2048).astype(np.float32)
streamer.send_audio_chunk(audio_chunk)

# Receive audio
while True:
    received_audio = streamer.get_audio_chunk(timeout=0.1)
    if received_audio is not None:
        print(f"Received audio: {len(received_audio)} samples")
        # Process received audio...

# Close connection
streamer.close()
```
