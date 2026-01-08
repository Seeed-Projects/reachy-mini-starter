# Reachy Mini SDK API 参考补充文档

本文档补充了 [API_REFERENCE_CN.md](API_REFERENCE_CN.md) 中遗漏的重要接口和功能。

---

## 目录

1. [ReachyMini 类补充接口](#1-reachymini-类补充接口)
2. [工具函数和辅助方法](#2-工具函数和辅助方法)
3. [插值算法详解](#3-插值算法详解)
4. [应用开发框架](#4-应用开发框架)
5. [录制动作系统](#5-录制动作系统)
6. [通信协议](#6-通信协议)
7. [IMU 数据接口](#7-imu-数据接口)
8. [上下文管理器](#8-上下文管理器)

---

## 1. ReachyMini 类补充接口

### 1.1 初始化参数详解

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

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `robot_name` | str | `"reachy_mini"` | 机器人名称，用于 Zenoh topic 命名空间 |
| `connection_mode` | `"auto" \| "localhost_only" \| "network"` | `"auto"` | 连接模式 |
| `spawn_daemon` | bool | `False` | 是否自动启动本地守护进程 |
| `use_sim` | bool | `False` | 是否使用仿真模式 |
| `timeout` | float | `5.0` | 连接超时时间（秒） |
| `automatic_body_yaw` | bool | `True` | 是否启用自动身体偏航计算 |
| `log_level` | str | `"INFO"` | 日志级别 |
| `media_backend` | str | `"default"` | 媒体后端类型 |
| `localhost_only` | Optional[bool] | `None` | **已弃用**，使用 `connection_mode` 代替 |

---

### 1.2 属性访问器

#### `media` 属性

```python
@property
def media(self) -> MediaManager
```

**说明**: 获取媒体管理器实例，用于访问摄像头和音频功能。

**返回**: `MediaManager` 实例

**示例**:
```python
with ReachyMini() as reachy:
    # 访问摄像头
    frame = reachy.media.get_frame()

    # 访问音频
    reachy.media.play_sound("test.wav")
```

---

#### `imu` 属性（仅无线版）

```python
@property
def imu(self) -> Dict[str, List[float] | float] | None
```

**说明**: 获取当前的 IMU 传感器数据。仅无线版本支持，Lite 版本返回 `None`。

**返回**: 包含以下键的字典，或 `None`

| 键 | 类型 | 说明 |
|----|------|------|
| `accelerometer` | `[x, y, z]` (m/s²) | 三轴加速度 |
| `gyroscope` | `[x, y, z]` (rad/s) | 三轴角速度 |
| `quaternion` | `[w, x, y, z]` | 方向四元数 |
| `temperature` | `float` (°C) | 温度 |

**注意**: 数据以 50Hz 频率缓存更新

**示例**:
```python
with ReachyMini() as reachy:
    if reachy.imu is not None:
        # 读取 IMU 数据
        accel = reachy.imu['accelerometer']
        gyro = reachy.imu['gyroscope']
        quat = reachy.imu['quaternion']
        temp = reachy.imu['temperature']

        print(f"加速度: {accel}")
        print(f"陀螺仪: {gyro}")
        print(f"四元数: {quat}")
        print(f"温度: {temp}°C")
```

---

### 1.3 look_at 系列方法

#### `look_at_image` - 看向图像中的点

```python
def look_at_image(
    self,
    u: int,
    v: int,
    duration: float = 1.0,
    perform_movement: bool = True
) -> npt.NDArray[np.float64]
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `u` | int | 图像中的水平像素坐标 |
| `v` | int | 图像中的垂直像素坐标 |
| `duration` | float | 运动持续时间（秒），0 表示立即到位 |
| `perform_movement` | bool | 是否执行运动，`False` 时仅计算并返回姿态 |

**返回**: `4x4` 头部姿态矩阵 (numpy array)

**示例**:
```python
with ReachyMini() as reachy:
    # 看向图像中心
    if reachy.media.camera:
        width, height = reachy.media.camera.resolution
        center_u = width // 2
        center_v = height // 2

        # 计算但不执行
        target_pose = reachy.look_at_image(
            u=center_u,
            v=center_v,
            duration=0,
            perform_movement=False
        )

        # 执行运动
        reachy.look_at_image(u=center_u, v=center_v, duration=1.0)
```

---

#### `look_at_world` - 看向 3D 空间中的点

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

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `x` | float | X 坐标（米），向前为正 |
| `y` | float | Y 坐标（米），向左为正 |
| `z` | float | Z 坐标（米），向上为正 |
| `duration` | float | 运动持续时间（秒） |
| `perform_movement` | bool | 是否执行运动 |

**返回**: `4x4` 头部姿态矩阵 (numpy array)

**示例**:
```python
with ReachyMini() as reachy:
    # 看向前方 0.5 米处
    reachy.look_at_world(x=0.5, y=0.0, z=0.0, duration=1.0)

    # 看向左上方
    reachy.look_at_world(x=0.3, y=0.2, z=0.1, duration=1.5)

    # 只计算姿态，不运动
    pose = reachy.look_at_world(
        x=0.5, y=0.0, z=0.0,
        duration=0,
        perform_movement=False
    )
    print(f"目标姿态矩阵:\n{pose}")
```

---

### 1.4 电机控制方法

#### `enable_motors` - 启用电机

```python
def enable_motors(self, ids: List[str] | None = None) -> None
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `ids` | List[str] \| None | 电机名称列表，`None` 表示全部 |

**电机名称** (与 `hardware_config.yaml` 对应):
- `"body_rotation"` - 身体旋转
- `"stewart_1"` ~ `"stewart_6"` - 斯图尔特平台关节
- `"right_antenna"` - 右天线
- `"left_antenna"` - 左天线

**示例**:
```python
with ReachyMini() as reachy:
    # 启用所有电机
    reachy.enable_motors()

    # 仅启用头部电机
    reachy.enable_motors(ids=["body_rotation", "stewart_1", "stewart_2"])

    # 仅启用天线
    reachy.enable_motors(ids=["right_antenna", "left_antenna"])
```

---

#### `disable_motors` - 禁用电机

```python
def disable_motors(self, ids: List[str] | None = None) -> None
```

**参数**: 同 `enable_motors`

**说明**: 禁用电机后，机器人可手动移动（自由模式）

**示例**:
```python
with ReachyMini() as reachy:
    # 禁用所有电机（可手动调整姿态）
    reachy.disable_motors()

    input("调整姿态后按回车继续...")

    # 重新启用电机
    reachy.enable_motors()
```

---

#### `enable_gravity_compensation` - 启用重力补偿

```python
def enable_gravity_compensation(self) -> None
```

**说明**: 启用重力补偿模式（电机模式 5），机器人会保持当前姿态同时抵抗重力。

**示例**:
```python
with ReachyMini() as reachy:
    # 启用重力补偿
    reachy.enable_gravity_compensation()

    # 机器人会保持姿态，但允许外部力推动
    input("按回车停止...")

    reachy.disable_gravity_compensation()
```

---

#### `disable_gravity_compensation` - 禁用重力补偿

```python
def disable_gravity_compensation(self) -> None
```

---

#### `set_automatic_body_yaw` - 设置自动身体偏航

```python
def set_automatic_body_yaw(self, body_yaw: float) -> None
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `body_yaw` | float | 身体偏航角度（弧度） |

**说明**: 设置用于逆运动学和正运动学计算的身体偏航角度。

**示例**:
```python
with ReachyMini() as reachy:
    import numpy as np

    # 设置身体偏航为 30 度
    reachy.set_automatic_body_yaw(np.radians(30))
```

---

### 1.5 录制功能

#### `start_recording` - 开始录制

```python
def start_recording(self) -> None
```

**说明**: 开始录制机器人的运动数据（头部姿态、天线位置、时间戳）。

**示例**:
```python
with ReachyMini() as reachy:
    reachy.start_recording()

    # 执行一些动作
    for i in range(10):
        pose = create_head_pose(z=0.05 * np.sin(i))
        reachy.set_target(head=pose)
        time.sleep(0.1)

    recorded_data = reachy.stop_recording()
    print(f"录制了 {len(recorded_data)} 帧数据")
```

---

#### `stop_recording` - 停止录制并获取数据

```python
def stop_recording(self) -> Optional[List[Dict[str, float | List[float] | List[List[float]]]]]
```

**返回**: 录制数据列表，每帧包含：

| 键 | 类型 | 说明 |
|----|------|------|
| `time` | float | 时间戳 |
| `head` | List[List[float]] | 4x4 头部姿态矩阵（扁平化） |
| `antennas` | List[float] | 天线角度 `[右, 左]` |
| `body_yaw` | float | 身体偏航角 |

**异常**: `RuntimeError` - 如果 5 秒内未收到数据

---

### 1.6 动作播放

#### `async_play_move` - 异步播放动作

```python
async def async_play_move(
    self,
    move: Move,
    play_frequency: float = 100.0,
    initial_goto_duration: float = 0.0,
    sound: bool = True
) -> None
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `move` | `Move` | - | 动作对象（`RecordedMove` 或自定义） |
| `play_frequency` | float | `100.0` | 播放频率 (Hz) |
| `initial_goto_duration` | float | `0.0` | 初始定位时间（秒），0 表示不定位 |
| `sound` | bool | `True` | 是否播放关联的声音 |

**示例**:
```python
from reachy_mini.motion.recorded_move import RecordedMoves

# 加载动作库
moves_library = RecordedMoves("pollen-robotics/reachy-mini-dances-library")

# 获取动作
dance_move = moves_library.get("another_one_bites_the_dust")

with ReachyMini() as reachy:
    # 异步播放
    import asyncio
    asyncio.run(reachy.async_play_move(dance_move))
```

---

#### `play_move` - 同步播放动作

```python
play_move = async_to_sync(async_play_move)
```

**说明**: `async_play_move` 的同步包装器。

**示例**:
```python
with ReachyMini() as reachy:
    # 同步播放
    reachy.play_move(dance_move, play_frequency=60.0)
```

---

### 1.7 获取关节位置

#### `get_present_antenna_joint_positions` - 获取当前天线关节位置

```python
def get_present_antenna_joint_positions(self) -> list[float]
```

**返回**: `[右天线角度, 左天线角度]` (弧度)

**示例**:
```python
with ReachyMini() as reachy:
    antennas = reachy.get_present_antenna_joint_positions()
    print(f"右天线: {np.degrees(antennas[0]):.1f}°")
    print(f"左天线: {np.degrees(antennas[1]):.1f}°")
```

---

### 1.8 头部姿态获取

#### `get_current_head_pose` - 获取当前头部姿态

```python
def get_current_head_pose(self) -> npt.NDArray[np.float64]
```

**返回**: `4x4` 齐次变换矩阵 (numpy array)

**示例**:
```python
with ReachyMini() as reachy:
    pose = reachy.get_current_head_pose()

    # 提取位置
    position = pose[:3, 3]

    # 提取旋转矩阵
    rotation = pose[:3, :3]

    # 转换为欧拉角
    from scipy.spatial.transform import Rotation as R
    euler = R.from_matrix(rotation).as_euler('xyz', degrees=True)

    print(f"位置: {position}")
    print(f"欧拉角: {euler}")
```

---

## 2. 工具函数和辅助方法

### 2.1 姿态创建

#### `create_head_pose` - 创建头部姿态矩阵

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

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `x, y, z` | float | `0` | 位置坐标 |
| `roll, pitch, yaw` | float | `0` | 姿态角度 |
| `mm` | bool | `False` | 为 `True` 时将毫米转换为米 |
| `degrees` | bool | `True` | 为 `True` 时角度使用度，否则弧度 |

**返回**: `4x4` 齐次变换矩阵

**示例**:
```python
from reachy_mini.utils import create_head_pose
import numpy as np

# 使用度（默认）
pose1 = create_head_pose(z=50, pitch=15)  # z 单位: mm，pitch 单位: 度

# 使用米和弧度
pose2 = create_head_pose(
    x=0.05, y=0.0, z=0.0,
    roll=0.0, pitch=np.radians(15), yaw=0.0,
    mm=False, degrees=False
)

# 使用 goto_target
with ReachyMini() as reachy:
    reachy.goto_target(head=pose1, duration=1.0)
```

---

## 3. 插值算法详解

### 3.1 插值技术类型

```python
from reachy_mini.utils.interpolation import InterpolationTechnique

class InterpolationTechnique(str, Enum):
    LINEAR = "linear"           # 线性插值
    MIN_JERK = "minjerk"        # 最小抖动插值（推荐）
    EASE_IN_OUT = "ease_in_out" # 缓动插值
    CARTOON = "cartoon"         # 卡通弹性插值
```

### 3.2 时间轨迹函数

```python
from reachy_mini.utils.interpolation import time_trajectory

value = time_trajectory(
    t: float,                                    # 时间 [0, 1]
    method: InterpolationTechnique = InterpolationTechnique.MIN_JERK
) -> float
```

**返回**: `[0, 1]` 范围内的插值时间值

**各方法特点**:
| 方法 | 特点 |
|------|------|
| `linear` | 匀速运动 |
| `minjerk` | 平滑起止，无突变（推荐） |
| `ease_in_out` | 缓入缓出 |
| `cartoon` | 弹性过冲效果 |

---

### 3.3 最小抖动插值

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

**说明**: 计算从起点到终点的最小抖动轨迹（5 次多项式）。

**参数**: 可选指定起止速度和加速度

**返回**: 可调用的插值函数 `f(t: float) -> ndarray`

**示例**:
```python
import numpy as np
from reachy_mini.utils.interpolation import minimum_jerk

start = np.array([0.0, 0.0, 0.0])
goal = np.array([0.5, 0.1, 0.2])

# 创建插值函数
traj = minimum_jerk(start, goal, duration=2.0)

# 在 t=1.0 时获取位置
pos_at_1s = traj(1.0)
print(f"1秒后的位置: {pos_at_1s}")
```

---

### 3.4 姿态插值

```python
from reachy_mini.utils.interpolation import linear_pose_interpolation

interpolated_pose = linear_pose_interpolation(
    start_pose: npt.NDArray[np.float64],    # 4x4 起始姿态
    target_pose: npt.NDArray[np.float64],   # 4x4 目标姿态
    t: float                                # 插值参数，通常 [0, 1]
) -> npt.NDArray[np.float64]
```

**说明**: 在两个 4x4 姿态矩阵之间进行线性插值。旋转部分使用球面线性插值，平移部分使用线性插值。

**注意**: `t` 可以超出 `[0, 1]` 范围实现过冲效果。

---

### 3.5 姿态距离计算

```python
from reachy_mini.utils.interpolation import distance_between_poses

trans_dist, angle_dist, unhinged_dist = distance_between_poses(
    pose1: npt.NDArray[np.float64],
    pose2: npt.NDArray[np.float64]
) -> Tuple[float, float, float]
```

**返回**:
| 返回值 | 类型 | 单位 | 说明 |
|--------|------|------|------|
| `trans_dist` | float | 米 | 平移距离 |
| `angle_dist` | float | 弧度 | 旋转角度 |
| `unhinged_dist` | float | 魔法毫米 | 平移(mm) + 旋转(度) |

---

### 3.6 世界坐标系偏移组合

```python
from reachy_mini.utils.interpolation import compose_world_offset

final_pose = compose_world_offset(
    T_abs: npt.NDArray[np.float64],       # 绝对姿态
    T_off_world: npt.NDArray[np.float64], # 世界坐标系偏移
    reorthonormalize: bool = False        # 是否重新正交化
) -> npt.NDArray[np.float64]
```

**说明**: 组合绝对姿态与世界坐标系偏移。

- 平移：`t_final = t_abs + t_off`
- 旋转：`R_final = R_off @ R_abs`

---

## 4. 应用开发框架

### 4.1 ReachyMiniApp 基类

```python
from reachy_mini.apps import ReachyMiniApp

class MyCustomApp(ReachyMiniApp):
    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event) -> None:
        """应用主逻辑"""
        while not stop_event.is_set():
            # 你的应用逻辑
            pass
```

**类属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| `custom_app_url` | str \| None | 自定义 Web 界面 URL |
| `dont_start_webserver` | bool | 是否禁用 Web 服务器 |
| `request_media_backend` | str \| None | 请求的媒体后端 |

---

### 4.2 应用生命周期

#### `wrapped_run` - 包装运行方法

```python
def wrapped_run(self, *args: Any, **kwargs: Any) -> None
```

**说明**: 自动处理 ReachyMini 连接、资源清理、Web 服务器启动等。

**自动功能**:
1. 检测本地守护进程可用性
2. 自动选择连接模式（本地/网络）
3. 设置媒体后端
4. 启动 FastAPI 设置服务器（如果配置）
5. 异常处理和清理

---

#### `stop` - 停止应用

```python
def stop(self) -> None
```

**说明**: 设置停止事件，优雅地终止应用。

**示例**:
```python
class MyApp(ReachyMiniApp):
    def run(self, reachy_mini, stop_event):
        # 在另一个线程中
        def signal_handler():
            input("按回车停止...")
            self.stop()

        import threading
        threading.Thread(target=signal_handler).start()

        while not stop_event.is_set():
            # 应用逻辑
            pass
```

---

#### `_check_daemon_on_localhost` - 检查本地守护进程

```python
@staticmethod
def _check_daemon_on_localhost(
    port: int = 8000,
    timeout: float = 0.5
) -> bool
```

**说明**: 检查指定端口是否有守护进程响应。

---

## 5. 录制动作系统

### 5.1 RecordedMove 类

```python
from reachy_mini.motion.recorded_move import RecordedMove

move = RecordedMove(
    move: Dict[str, Any],              # 动作数据字典
    sound_path: Optional[Path] = None  # 关联的声音文件
)
```

**属性**:
| 属性 | 类型 | 说明 |
|------|------|------|
| `description` | str | 动作描述 |
| `timestamps` | List[float] | 时间戳列表 |
| `trajectory` | List[Dict] | 轨迹数据 |
| `duration` | float | 动作时长（只读） |
| `sound_path` | Optional[Path] | 声音文件路径（只读） |

---

#### `evaluate` - 评估动作

```python
def evaluate(self, t: float) -> tuple[
    npt.NDArray[np.float64],  # 头部姿态 (4x4)
    npt.NDArray[np.float64],  # 天线位置 [右, 左]
    float                     # 身体偏航
]
```

**说明**: 计算时间 `t` 时的头部姿态、天线位置和身体偏航。

**异常**: `Exception` - 如果 `t` 超出动作时长

---

### 5.2 RecordedMoves 类 - 动作库

```python
from reachy_mini.motion.recorded_move import RecordedMoves

library = RecordedMoves(
    hf_dataset_name: str  # HuggingFace 数据集名称
)
```

**示例**:
```python
# 加载官方动作库
library = RecordedMoves("pollen-robotics/reachy-mini-dances-library")

# 列出所有动作
moves = library.list_moves()
print(f"可用动作: {moves}")

# 获取特定动作
dance = library.get("another_one_bites_the_dust")

# 播放
with ReachyMini() as reachy:
    reachy.play_move(dance)
```

---

#### `list_moves` - 列出动作

```python
def list_moves(self) -> List[str]
```

**返回**: 动作名称列表

---

#### `get` - 获取动作

```python
def get(self, move_name: str) -> RecordedMove
```

**异常**: `ValueError` - 如果动作不存在

---

### 5.3 线性插值函数

```python
from reachy_mini.motion.recorded_move import lerp

value = lerp(v0: float, v1: float, alpha: float) -> float
```

**说明**: 标准线性插值：`v0 + alpha * (v1 - v0)`

---

## 6. 通信协议

### 6.1 任务请求协议

#### GotoTaskRequest - Goto 任务请求

```python
from reachy_mini.io.protocol import GotoTaskRequest

request = GotoTaskRequest(
    head: list[float] | None,         # 4x4 扁平化姿态矩阵
    antennas: list[float] | None,     # [右, 左] 弧度
    duration: float,                   # 持续时间
    method: InterpolationTechnique,   # 插值方法
    body_yaw: float | None             # 身体偏航
)
```

---

#### PlayMoveTaskRequest - 播放动作任务请求

```python
from reachy_mini.io.protocol import PlayMoveTaskRequest

request = PlayMoveTaskRequest(
    move_name: str  # 动作名称
)
```

---

#### TaskRequest - 通用任务请求

```python
from reachy_mini.io.protocol import TaskRequest
from datetime import datetime
from uuid import UUID, uuid4

task = TaskRequest(
    uuid: UUID,                    # 任务唯一 ID
    req: AnyTaskRequest,           # Goto 或 PlayMove
    timestamp: datetime            # 时间戳
)

# 创建新任务
task = TaskRequest(
    uuid=uuid4(),
    req=GotoTaskRequest(...),
    timestamp=datetime.now()
)
```

---

#### TaskProgress - 任务进度

```python
from reachy_mini.io.protocol import TaskProgress

progress = TaskProgress(
    uuid: UUID,              # 任务 ID
    finished: bool = False,  # 是否完成
    error: str | None = None,  # 错误信息
    timestamp: datetime      # 时间戳
)
```

---

## 7. IMU 数据接口（仅无线版）

### 7.1 获取 IMU 数据

```python
with ReachyMini() as reachy:
    imu_data = reachy.imu

    if imu_data is not None:
        # 加速度计 (m/s²)
        accel_x, accel_y, accel_z = imu_data['accelerometer']

        # 陀螺仪 (rad/s)
        gyro_x, gyro_y, gyro_z = imu_data['gyroscope']

        # 四元数 [w, x, y, z]
        quat_w, quat_x, quat_y, quat_z = imu_data['quaternion']

        # 温度 (°C)
        temperature = imu_data['temperature']

        # 转换四元数为欧拉角
        from scipy.spatial.transform import Rotation as R
        r = R.from_quat([quat_x, quat_y, quat_z, quat_w])
        euler = r.as_euler('xyz', degrees=True)

        print(f"Roll: {euler[0]:.1f}°")
        print(f"Pitch: {euler[1]:.1f}°")
        print(f"Yaw: {euler[2]:.1f}°")
```

### 7.2 使用场景

| 场景 | 说明 |
|------|------|
| **姿态平衡** | 使用陀螺仪数据检测倾斜 |
| **运动检测** | 检测机器人是否被移动 |
| **方向保持** | 使用四元数保持朝向 |
| **震动检测** | 监控加速度计异常 |

---

## 8. 上下文管理器

### 8.1 使用 with 语句

```python
# 推荐：使用上下文管理器
with ReachyMini() as reachy:
    # 你的代码
    reachy.goto_target(head=create_head_pose(z=10), duration=1.0)
# 自动清理资源

# 等价于
reachy = ReachyMini()
try:
    reachy.goto_target(head=create_head_pose(z=10), duration=1.0)
finally:
    reachy.media.close()
    reachy.client.disconnect()
```

### 8.2 上下文管理器方法

| 方法 | 说明 |
|------|------|
| `__enter__` | 进入上下文，返回 `self` |
| `__exit__` | 退出上下文，清理资源 |
| `__del__` | 析构函数，确保断开连接 |

---

## 附录

### A. 完整示例：综合应用

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
from reachy_mini.motion.recorded_move import RecordedMoves
import numpy as np
import time

def comprehensive_example():
    """综合示例展示多个功能"""

    with ReachyMini(
        connection_mode="auto",
        timeout=10.0
    ) as reachy:

        # 1. 检查 IMU
        if reachy.imu is not None:
            print("✅ IMU 可用")
            quat = reachy.imu['quaternion']
            print(f"   四元数: {quat}")

        # 2. 启用重力补偿
        print("启用重力补偿...")
        reachy.enable_gravity_compensation()
        time.sleep(2)
        reachy.disable_gravity_compensation()

        # 3. 创建并设置姿态
        print("移动到目标姿态...")
        target = create_head_pose(z=30, pitch=10, mm=True)
        reachy.goto_target(head=target, duration=2.0)

        # 4. 看向世界坐标点
        print("看向目标点...")
        reachy.look_at_world(x=0.3, y=0.1, z=0.1, duration=1.5)

        # 5. 获取当前状态
        pose = reachy.get_current_head_pose()
        head_joints, antenna_joints = reachy.get_current_joint_positions()
        print(f"头部关节: {head_joints}")
        print(f"天线角度: {antenna_joints}")

        # 6. 播放声音
        reachy.media.play_sound("wake_up.wav")

        # 7. 获取摄像头画面
        frame = reachy.media.get_frame()
        if frame is not None:
            print(f"摄像头分辨率: {frame.shape}")

        # 8. 看向图像中心
        if reachy.media.camera:
            w, h = reachy.media.camera.resolution
            reachy.look_at_image(u=w//2, v=h//2, duration=1.0)

        # 9. 播放录制动作
        try:
            lib = RecordedMoves("pollen-robotics/reachy-mini-dances-library")
            moves = lib.list_moves()
            if moves:
                dance = lib.get(moves[0])
                reachy.play_move(dance, play_frequency=60.0)
        except Exception as e:
            print(f"无法播放动作: {e}")

if __name__ == "__main__":
    comprehensive_example()
```

### B. 文件参考

| 模块 | 文件路径 | 主要功能 |
|------|---------|---------|
| ReachyMini | `src/reachy_mini/reachy_mini.py` | SDK 主类 |
| 媒体管理 | `src/reachy_mini/media/media_manager.py` | 摄像头/音频管理 |
| 插值工具 | `src/reachy_mini/utils/interpolation.py` | 插值算法 |
| 工具函数 | `src/reachy_mini/utils/__init__.py` | 姿态创建等 |
| 录制动作 | `src/reachy_mini/motion/recorded_move.py` | 动作录制/播放 |
| 应用框架 | `src/reachy_mini/apps/app.py` | 应用基类 |
| 通信协议 | `src/reachy_mini/io/protocol.py` | 协议定义 |

---

**文档版本**: 1.0
**最后更新**: 2025-01-08
**适用 SDK 版本**: reachy_mini >= 1.2.0
