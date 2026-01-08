# Reachy Mini SDK API Reference Supplement

This document supplements important interfaces and features missing from [API_REFERENCE.md](API_REFERENCE.md).

---

## Table of Contents

1. [ReachyMini Class Supplementary Interfaces](#1-reachymini-class-supplementary-interfaces)
2. [Utility Functions and Helper Methods](#2-utility-functions-and-helper-methods)
3. [Interpolation Algorithms Explained](#3-interpolation-algorithms-explained)
4. [Application Development Framework](#4-application-development-framework)
5. [Motion Recording System](#5-motion-recording-system)
6. [Communication Protocols](#6-communication-protocols)
7. [IMU Data Interface](#7-imu-data-interface)
8. [Context Managers](#8-context-managers)

---

## 1. ReachyMini Class Supplementary Interfaces

### 1.1 Initialization Parameters Detailed

```python
from reachy_mini import ReachyMini

ReachyMini(
    robot_name: str = "reachy_mini",
    connection_mode: ConnectionMode = "auto",
    spawn_daemon: bool = False,
    use_sim: bool = False,
    timeout: float = 5.0,
    automatic_body_yaw: bool = True,
    log_level: str = "INFO",
    media_backend: str = "default",
    localhost_only: Optional[bool] = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `robot_name` | str | `"reachy_mini"` | Robot name, used for Zenoh topic namespace |
| `connection_mode` | `"auto" \| "localhost_only" \| "network"` | `"auto"` | Connection mode |
| `spawn_daemon` | bool | `False` | Whether to auto-start local daemon |
| `use_sim` | bool | `False` | Whether to use simulation mode |
| `timeout` | float | `5.0` | Connection timeout (seconds) |
| `automatic_body_yaw` | bool | `True` | Whether to enable automatic body yaw calculation |
| `log_level` | str | `"INFO"` | Log level |
| `media_backend` | str | `"default"` | Media backend type |
| `localhost_only` | Optional[bool] | `None` | **Deprecated**, use `connection_mode` instead |

---

### 1.2 Property Accessors

#### `media` Property

```python
@property
def media(self) -> MediaManager
```

**Description**: Get media manager instance for accessing camera and audio features.

**Returns**: `MediaManager` instance

**Example**:
```python
with ReachyMini() as reachy:
    # Access camera
    frame = reachy.media.get_frame()

    # Access audio
    reachy.media.play_sound("test.wav")
```

---

#### `imu` Property (Wireless Version Only)

```python
@property
def imu(self) -> Dict[str, List[float] | float] | None
```

**Description**: Get current IMU sensor data. Only supported on wireless version; returns `None` on Lite version.

**Returns**: Dictionary with following keys, or `None`

| Key | Type | Description |
|-----|------|-------------|
| `accelerometer` | `[x, y, z]` (m/s²) | Three-axis acceleration |
| `gyroscope` | `[x, y, z]` (rad/s) | Three-axis angular velocity |
| `quaternion` | `[w, x, y, z]` | Orientation quaternion |
| `temperature` | `float` (°C) | Temperature |

**Note**: Data is cached and updated at 50Hz frequency

**Example**:
```python
with ReachyMini() as reachy:
    if reachy.imu is not None:
        # Read IMU data
        accel = reachy.imu['accelerometer']
        gyro = reachy.imu['gyroscope']
        quat = reachy.imu['quaternion']
        temp = reachy.imu['temperature']

        print(f"Acceleration: {accel}")
        print(f"Gyroscope: {gyro}")
        print(f"Quaternion: {quat}")
        print(f"Temperature: {temp}°C")
```

---

### 1.3 look_at Series Methods

#### `look_at_image` - Look at Point in Image

```python
def look_at_image(
    self,
    u: int,
    v: int,
    duration: float = 1.0,
    perform_movement: bool = True
) -> npt.NDArray[np.float64]
```

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `u` | int | Horizontal pixel coordinate in image |
| `v` | int | Vertical pixel coordinate in image |
| `duration` | float | Movement duration (seconds), 0 means immediate |
| `perform_movement` | bool | Whether to execute movement, `False` only calculates and returns pose |

**Returns**: `4x4` head pose matrix (numpy array)

**Example**:
```python
with ReachyMini() as reachy:
    # Look at image center
    if reachy.media.camera:
        width, height = reachy.media.camera.resolution
        center_u = width // 2
        center_v = height // 2

        # Calculate without executing
        target_pose = reachy.look_at_image(
            u=center_u,
            v=center_v,
            duration=0,
            perform_movement=False
        )

        # Execute movement
        reachy.look_at_image(u=center_u, v=center_v, duration=1.0)
```

---

#### `look_at_world` - Look at Point in 3D Space

```python
def look_at_world(
    self,
    x: float,
    y: float,
    z: float,
    duration: float = 1.0,
    perform_movement: bool = True
) -> npt.NDArray[np.float64]
```

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `x` | float | X coordinate (meters), forward is positive |
| `y` | float | Y coordinate (meters), left is positive |
| `z` | float | Z coordinate (meters), up is positive |
| `duration` | float | Movement duration (seconds) |
| `perform_movement` | bool | Whether to execute movement |

**Returns**: `4x4` head pose matrix (numpy array)

**Example**:
```python
with ReachyMini() as reachy:
    # Look at point 0.5m in front
    reachy.look_at_world(x=0.5, y=0.0, z=0.0, duration=1.0)

    # Look at upper-left
    reachy.look_at_world(x=0.3, y=0.2, z=0.1, duration=1.5)

    # Only calculate pose, don't move
    pose = reachy.look_at_world(
        x=0.5, y=0.0, z=0.0,
        duration=0,
        perform_movement=False
    )
    print(f"Target pose matrix:\n{pose}")
```

---

### 1.4 Motor Control Methods

#### `enable_motors` - Enable Motors

```python
def enable_motors(self, ids: List[str] | None = None) -> None
```

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `ids` | List[str] \| None | List of motor names, `None` means all |

**Motor Names** (corresponding to `hardware_config.yaml`):
- `"body_rotation"` - Body rotation
- `"stewart_1"` ~ `"stewart_6"` - Stewart platform joints
- `"right_antenna"` - Right antenna
- `"left_antenna"` - Left antenna

**Example**:
```python
with ReachyMini() as reachy:
    # Enable all motors
    reachy.enable_motors()

    # Enable only head motors
    reachy.enable_motors(ids=["body_rotation", "stewart_1", "stewart_2"])

    # Enable only antennas
    reachy.enable_motors(ids=["right_antenna", "left_antenna"])
```

---

#### `disable_motors` - Disable Motors

```python
def disable_motors(self, ids: List[str] | None = None) -> None
```

**Parameters**: Same as `enable_motors`

**Description**: After disabling motors, robot can be moved manually (freed mode)

**Example**:
```python
with ReachyMini() as reachy:
    # Disable all motors (can manually adjust pose)
    reachy.disable_motors()

    input("Press Enter after adjusting pose...")

    # Re-enable motors
    reachy.enable_motors()
```

---

#### `enable_gravity_compensation` - Enable Gravity Compensation

```python
def enable_gravity_compensation(self) -> None
```

**Description**: Enable gravity compensation mode (motor mode 5), robot maintains current pose while resisting gravity.

**Example**:
```python
with ReachyMini() as reachy:
    # Enable gravity compensation
    reachy.enable_gravity_compensation()

    # Robot maintains pose but allows external force to push
    input("Press Enter to stop...")

    reachy.disable_gravity_compensation()
```

---

#### `disable_gravity_compensation` - Disable Gravity Compensation

```python
def disable_gravity_compensation(self) -> None
```

---

#### `set_automatic_body_yaw` - Set Automatic Body Yaw

```python
def set_automatic_body_yaw(self, body_yaw: float) -> None
```

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `body_yaw` | float | Body yaw angle (radians) |

**Description**: Set body yaw angle used for inverse and forward kinematics calculations.

**Example**:
```python
with ReachyMini() as reachy:
    import numpy as np

    # Set body yaw to 30 degrees
    reachy.set_automatic_body_yaw(np.radians(30))
```

---

### 1.5 Recording Functions

#### `start_recording` - Start Recording

```python
def start_recording(self) -> None
```

**Description**: Start recording robot motion data (head pose, antenna positions, timestamps).

**Example**:
```python
with ReachyMini() as reachy:
    reachy.start_recording()

    # Perform some movements
    for i in range(10):
        pose = create_head_pose(z=0.05 * np.sin(i))
        reachy.set_target(head=pose)
        time.sleep(0.1)

    recorded_data = reachy.stop_recording()
    print(f"Recorded {len(recorded_data)} frames")
```

---

#### `stop_recording` - Stop Recording and Get Data

```python
def stop_recording(self) -> Optional[List[Dict[str, float | List[float] | List[List[float]]]]]
```

**Returns**: List of recorded data, each frame contains:

| Key | Type | Description |
|-----|------|-------------|
| `time` | float | Timestamp |
| `head` | List[List[float]] | 4x4 head pose matrix (flattened) |
| `antennas` | List[float] | Antenna angles `[right, left]` |
| `body_yaw` | float | Body yaw angle |

**Exception**: `RuntimeError` - If no data received within 5 seconds

---

### 1.6 Motion Playback

#### `async_play_move` - Async Play Move

```python
async def async_play_move(
    self,
    move: Move,
    play_frequency: float = 100.0,
    initial_goto_duration: float = 0.0,
    sound: bool = True
) -> None
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `move` | `Move` | - | Move object (`RecordedMove` or custom) |
| `play_frequency` | float | `100.0` | Playback frequency (Hz) |
| `initial_goto_duration` | float | `0.0` | Initial positioning time (seconds), 0 means no positioning |
| `sound` | bool | `True` | Whether to play associated sound |

**Example**:
```python
from reachy_mini.motion.recorded_move import RecordedMoves

# Load move library
moves_library = RecordedMoves("pollen-robotics/reachy-mini-dances-library")

# Get move
dance_move = moves_library.get("another_one_bites_the_dust")

with ReachyMini() as reachy:
    # Async playback
    import asyncio
    asyncio.run(reachy.async_play_move(dance_move))
```

---

#### `play_move` - Sync Play Move

```python
play_move = async_to_sync(async_play_move)
```

**Description**: Synchronous wrapper for `async_play_move`.

**Example**:
```python
with ReachyMini() as reachy:
    # Sync playback
    reachy.play_move(dance_move, play_frequency=60.0)
```

---

### 1.7 Getting Joint Positions

#### `get_present_antenna_joint_positions` - Get Current Antenna Joint Positions

```python
def get_present_antenna_joint_positions(self) -> list[float]
```

**Returns**: `[right_antenna_angle, left_antenna_angle]` (radians)

**Example**:
```python
with ReachyMini() as reachy:
    antennas = reachy.get_present_antenna_joint_positions()
    print(f"Right antenna: {np.degrees(antennas[0]):.1f}°")
    print(f"Left antenna: {np.degrees(antennas[1]):.1f}°")
```

---

### 1.8 Head Pose Retrieval

#### `get_current_head_pose` - Get Current Head Pose

```python
def get_current_head_pose(self) -> npt.NDArray[np.float64]
```

**Returns**: `4x4` homogeneous transformation matrix (numpy array)

**Example**:
```python
with ReachyMini() as reachy:
    pose = reachy.get_current_head_pose()

    # Extract position
    position = pose[:3, 3]

    # Extract rotation matrix
    rotation = pose[:3, :3]

    # Convert to Euler angles
    from scipy.spatial.transform import Rotation as R
    euler = R.from_matrix(rotation).as_euler('xyz', degrees=True)

    print(f"Position: {position}")
    print(f"Euler angles: {euler}")
```

---

## 2. Utility Functions and Helper Methods

### 2.1 Pose Creation

#### `create_head_pose` - Create Head Pose Matrix

```python
from reachy_mini.utils import create_head_pose

pose = create_head_pose(
    x: float = 0,
    y: float = 0,
    z: float = 0,
    roll: float = 0,
    pitch: float = 0,
    yaw: float = 0,
    mm: bool = False,
    degrees: bool = True
) -> npt.NDArray[np.float64]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x, y, z` | float | `0` | Position coordinates |
| `roll, pitch, yaw` | float | `0` | Orientation angles |
| `mm` | bool | `False` | When `True`, converts millimeters to meters |
| `degrees` | bool | `True` | When `True`, angles use degrees, otherwise radians |

**Returns**: `4x4` homogeneous transformation matrix

**Example**:
```python
from reachy_mini.utils import create_head_pose
import numpy as np

# Using degrees (default)
pose1 = create_head_pose(z=50, pitch=15)  # z unit: mm, pitch unit: degrees

# Using meters and radians
pose2 = create_head_pose(
    x=0.05, y=0.0, z=0.0,
    roll=0.0, pitch=np.radians(15), yaw=0.0,
    mm=False, degrees=False
)

# Using goto_target
with ReachyMini() as reachy:
    reachy.goto_target(head=pose1, duration=1.0)
```

---

## 3. Interpolation Algorithms Explained

### 3.1 Interpolation Technique Types

```python
from reachy_mini.utils.interpolation import InterpolationTechnique

class InterpolationTechnique(str, Enum):
    LINEAR = "linear"           # Linear interpolation
    MIN_JERK = "minjerk"        # Minimum jerk interpolation (recommended)
    EASE_IN_OUT = "ease_in_out" # Ease-in-out interpolation
    CARTOON = "cartoon"         # Cartoon elastic interpolation
```

### 3.2 Time Trajectory Functions

```python
from reachy_mini.utils.interpolation import time_trajectory

value = time_trajectory(
    t: float,                                    # Time [0, 1]
    method: InterpolationTechnique = InterpolationTechnique.MIN_JERK
) -> float
```

**Returns**: Interpolated time value in range `[0, 1]`

**Method Characteristics**:
| Method | Characteristics |
|--------|----------------|
| `linear` | Constant velocity |
| `minjerk` | Smooth start/stop, no discontinuities (recommended) |
| `ease_in_out` | Ease-in, ease-out |
| `cartoon` | Elastic overshoot effect |

---

### 3.3 Minimum Jerk Interpolation

```python
from reachy_mini.utils.interpolation import minimum_jerk

interpolation_func = minimum_jerk(
    starting_position: npt.NDArray[np.float64],
    goal_position: npt.NDArray[np.float64],
    duration: float,
    starting_velocity: Optional[npt.NDArray[np.float64]] = None,
    starting_acceleration: Optional[npt.NDArray[np.float64]] = None,
    final_velocity: Optional[npt.NDArray[np.float64]] = None,
    final_acceleration: Optional[npt.NDArray[np.float64]] = None
) -> InterpolationFunc
```

**Description**: Calculate minimum jerk trajectory from start to goal (5th degree polynomial).

**Parameters**: Optionally specify start/end velocities and accelerations

**Returns**: Callable interpolation function `f(t: float) -> ndarray`

**Example**:
```python
import numpy as np
from reachy_mini.utils.interpolation import minimum_jerk

start = np.array([0.0, 0.0, 0.0])
goal = np.array([0.5, 0.1, 0.2])

# Create interpolation function
traj = minimum_jerk(start, goal, duration=2.0)

# Get position at t=1.0
pos_at_1s = traj(1.0)
print(f"Position after 1 second: {pos_at_1s}")
```

---

### 3.4 Pose Interpolation

```python
from reachy_mini.utils.interpolation import linear_pose_interpolation

interpolated_pose = linear_pose_interpolation(
    start_pose: npt.NDArray[np.float64],    # 4x4 start pose
    target_pose: npt.NDArray[np.float64],   # 4x4 target pose
    t: float                                # Interpolation parameter, typically [0, 1]
) -> npt.NDArray[np.float64]
```

**Description**: Linearly interpolate between two 4x4 pose matrices. Rotation part uses spherical linear interpolation, translation part uses linear interpolation.

**Note**: `t` can exceed `[0, 1]` range for overshoot effects.

---

### 3.5 Pose Distance Calculation

```python
from reachy_mini.utils.interpolation import distance_between_poses

trans_dist, angle_dist, unhinged_dist = distance_between_poses(
    pose1: npt.NDArray[np.float64],
    pose2: npt.NDArray[np.float64]
) -> Tuple[float, float, float]
```

**Returns**:
| Return Value | Type | Unit | Description |
|--------------|------|------|-------------|
| `trans_dist` | float | meters | Translation distance |
| `angle_dist` | float | radians | Rotation angle |
| `unhinged_dist` | float | magic millimeters | Translation(mm) + Rotation(degrees) |

---

### 3.6 World Coordinate Frame Offset Composition

```python
from reachy_mini.utils.interpolation import compose_world_offset

final_pose = compose_world_offset(
    T_abs: npt.NDArray[np.float64],       # Absolute pose
    T_off_world: npt.NDArray[np.float64], # World frame offset
    reorthonormalize: bool = False        # Whether to re-orthonormalize
) -> npt.NDArray[np.float64]
```

**Description**: Compose absolute pose with world frame offset.

- Translation: `t_final = t_abs + t_off`
- Rotation: `R_final = R_off @ R_abs`

---

## 4. Application Development Framework

### 4.1 ReachyMiniApp Base Class

```python
from reachy_mini.apps import ReachyMiniApp

class MyCustomApp(ReachyMiniApp):
    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        """Application main logic"""
        while not stop_event.is_set():
            # Your application logic
            pass
```

**Class Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| `custom_app_url` | str \| None | Custom web interface URL |
| `dont_start_webserver` | bool | Whether to disable web server |
| `request_media_backend` | str \| None | Requested media backend |

---

### 4.2 Application Lifecycle

#### `wrapped_run` - Wrapped Run Method

```python
def wrapped_run(self, *args: Any, **kwargs: Any) -> None
```

**Description**: Automatically handles ReachyMini connection, resource cleanup, web server startup, etc.

**Automatic Features**:
1. Detect local daemon availability
2. Auto-select connection mode (local/network)
3. Set up media backend
4. Start FastAPI setup server (if configured)
5. Exception handling and cleanup

---

#### `stop` - Stop Application

```python
def stop(self) -> None
```

**Description**: Set stop event, gracefully terminate application.

**Example**:
```python
class MyApp(ReachyMiniApp):
    def run(self, reachy_mini, stop_event):
        # In another thread
        def signal_handler():
            input("Press Enter to stop...")
            self.stop()

        import threading
        threading.Thread(target=signal_handler).start()

        while not stop_event.is_set():
            # Application logic
            pass
```

---

#### `_check_daemon_on_localhost` - Check Local Daemon

```python
@staticmethod
def _check_daemon_on_localhost(
    port: int = 8000,
    timeout: float = 0.5
) -> bool
```

**Description**: Check if daemon responds on specified port.

---

## 5. Motion Recording System

### 5.1 RecordedMove Class

```python
from reachy_mini.motion.recorded_move import RecordedMove

move = RecordedMove(
    move: Dict[str, Any],              # Move data dictionary
    sound_path: Optional[Path] = None  # Associated sound file
)
```

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| `description` | str | Move description |
| `timestamps` | List[float] | List of timestamps |
| `trajectory` | List[Dict] | Trajectory data |
| `duration` | float | Move duration (read-only) |
| `sound_path` | Optional[Path] | Sound file path (read-only) |

---

#### `evaluate` - Evaluate Move

```python
def evaluate(self, t: float) -> tuple[
    npt.NDArray[np.float64],  # Head pose (4x4)
    npt.NDArray[np.float64],  # Antenna positions [right, left]
    float                     # Body yaw
]
```

**Description**: Calculate head pose, antenna positions, and body yaw at time `t`.

**Exception**: `Exception` - If `t` exceeds move duration

---

### 5.2 RecordedMoves Class - Move Library

```python
from reachy_mini.motion.recorded_move import RecordedMoves

library = RecordedMoves(
    hf_dataset_name: str  # HuggingFace dataset name
)
```

**Example**:
```python
# Load official move library
library = RecordedMoves("pollen-robotics/reachy-mini-dances-library")

# List all moves
moves = library.list_moves()
print(f"Available moves: {moves}")

# Get specific move
dance = library.get("another_one_bites_the_dust")

# Play
with ReachyMini() as reachy:
    reachy.play_move(dance)
```

---

#### `list_moves` - List Moves

```python
def list_moves(self) -> List[str]
```

**Returns**: List of move names

---

#### `get` - Get Move

```python
def get(self, move_name: str) -> RecordedMove
```

**Exception**: `ValueError` - If move doesn't exist

---

### 5.3 Linear Interpolation Function

```python
from reachy_mini.motion.recorded_move import lerp

value = lerp(v0: float, v1: float, alpha: float) -> float
```

**Description**: Standard linear interpolation: `v0 + alpha * (v1 - v0)`

---

## 6. Communication Protocols

### 6.1 Task Request Protocols

#### GotoTaskRequest - Goto Task Request

```python
from reachy_mini.io.protocol import GotoTaskRequest

request = GotoTaskRequest(
    head: list[float] | None,         # 4x4 flattened pose matrix
    antennas: list[float] | None,     # [right, left] in radians
    duration: float,                   # Duration
    method: InterpolationTechnique,   # Interpolation method
    body_yaw: float | None             # Body yaw
)
```

---

#### PlayMoveTaskRequest - Play Move Task Request

```python
from reachy_mini.io.protocol import PlayMoveTaskRequest

request = PlayMoveTaskRequest(
    move_name: str  # Move name
)
```

---

#### TaskRequest - Generic Task Request

```python
from reachy_mini.io.protocol import TaskRequest
from datetime import datetime
from uuid import UUID, uuid4

task = TaskRequest(
    uuid: UUID,                    # Task unique ID
    req: AnyTaskRequest,           # Goto or PlayMove
    timestamp: datetime            # Timestamp
)

# Create new task
task = TaskRequest(
    uuid=uuid4(),
    req=GotoTaskRequest(...),
    timestamp=datetime.now()
)
```

---

#### TaskProgress - Task Progress

```python
from reachy_mini.io.protocol import TaskProgress

progress = TaskProgress(
    uuid: UUID,              # Task ID
    finished: bool = False,  # Whether finished
    error: str | None = None,  # Error message
    timestamp: datetime      # Timestamp
)
```

---

## 7. IMU Data Interface (Wireless Version Only)

### 7.1 Getting IMU Data

```python
with ReachyMini() as reachy:
    imu_data = reachy.imu

    if imu_data is not None:
        # Accelerometer (m/s²)
        accel_x, accel_y, accel_z = imu_data['accelerometer']

        # Gyroscope (rad/s)
        gyro_x, gyro_y, gyro_z = imu_data['gyroscope']

        # Quaternion [w, x, y, z]
        quat_w, quat_x, quat_y, quat_z = imu_data['quaternion']

        # Temperature (°C)
        temperature = imu_data['temperature']

        # Convert quaternion to Euler angles
        from scipy.spatial.transform import Rotation as R
        r = R.from_quat([quat_x, quat_y, quat_z, quat_w])
        euler = r.as_euler('xyz', degrees=True)

        print(f"Roll: {euler[0]:.1f}°")
        print(f"Pitch: {euler[1]:.1f}°")
        print(f"Yaw: {euler[2]:.1f}°")
```

### 7.2 Use Cases

| Use Case | Description |
|----------|-------------|
| **Pose Balance** | Use gyroscope data to detect tilt |
| **Motion Detection** | Detect if robot is being moved |
| **Orientation Hold** | Use quaternion to maintain heading |
| **Vibration Detection** | Monitor accelerometer anomalies |

---

## 8. Context Managers

### 8.1 Using with Statement

```python
# Recommended: Use context manager
with ReachyMini() as reachy:
    # Your code
    reachy.goto_target(head=create_head_pose(z=10), duration=1.0)
# Automatically cleanup resources

# Equivalent to
reachy = ReachyMini()
try:
    reachy.goto_target(head=create_head_pose(z=10), duration=1.0)
finally:
    reachy.media.close()
    reachy.client.disconnect()
```

### 8.2 Context Manager Methods

| Method | Description |
|--------|-------------|
| `__enter__` | Enter context, return `self` |
| `__exit__` | Exit context, cleanup resources |
| `__del__` | Destructor, ensure disconnection |

---

## Appendix

### A. Complete Example: Comprehensive Application

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
from reachy_mini.motion.recorded_move import RecordedMoves
import numpy as np
import time

def comprehensive_example():
    """Comprehensive example showing multiple features"""

    with ReachyMini(
        connection_mode="auto",
        timeout=10.0
    ) as reachy:

        # 1. Check IMU
        if reachy.imu is not None:
            print("✅ IMU available")
            quat = reachy.imu['quaternion']
            print(f"   Quaternion: {quat}")

        # 2. Enable gravity compensation
        print("Enabling gravity compensation...")
        reachy.enable_gravity_compensation()
        time.sleep(2)
        reachy.disable_gravity_compensation()

        # 3. Create and set pose
        print("Moving to target pose...")
        target = create_head_pose(z=30, pitch=10, mm=True)
        reachy.goto_target(head=target, duration=2.0)

        # 4. Look at world coordinate point
        print("Looking at target point...")
        reachy.look_at_world(x=0.3, y=0.1, z=0.1, duration=1.5)

        # 5. Get current state
        pose = reachy.get_current_head_pose()
        head_joints, antenna_joints = reachy.get_current_joint_positions()
        print(f"Head joints: {head_joints}")
        print(f"Antenna angles: {antenna_joints}")

        # 6. Play sound
        reachy.media.play_sound("wake_up.wav")

        # 7. Get camera frame
        frame = reachy.media.get_frame()
        if frame is not None:
            print(f"Camera resolution: {frame.shape}")

        # 8. Look at image center
        if reachy.media.camera:
            w, h = reachy.media.camera.resolution
            reachy.look_at_image(u=w//2, v=h//2, duration=1.0)

        # 9. Play recorded move
        try:
            lib = RecordedMoves("pollen-robotics/reachy-mini-dances-library")
            moves = lib.list_moves()
            if moves:
                dance = lib.get(moves[0])
                reachy.play_move(dance, play_frequency=60.0)
        except Exception as e:
            print(f"Cannot play move: {e}")

if __name__ == "__main__":
    comprehensive_example()
```

### B. File References

| Module | File Path | Main Functions |
|--------|-----------|----------------|
| ReachyMini | `src/reachy_mini/reachy_mini.py` | SDK main class |
| Media Manager | `src/reachy_mini/media/media_manager.py` | Camera/audio management |
| Interpolation Utils | `src/reachy_mini/utils/interpolation.py` | Interpolation algorithms |
| Utility Functions | `src/reachy_mini/utils/__init__.py` | Pose creation, etc. |
| Recorded Moves | `src/reachy_mini/motion/recorded_move.py` | Move recording/playback |
| Application Framework | `src/reachy_mini/apps/app.py` | Application base class |
| Communication Protocol | `src/reachy_mini/io/protocol.py` | Protocol definitions |

---

**Document Version**: 1.0
**Last Updated**: 2025-01-08
**Applicable SDK Version**: reachy_mini >= 1.2.0
