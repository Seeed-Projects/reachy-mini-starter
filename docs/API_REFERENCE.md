# Reachy Mini Python SDK API 参考文档

本文档详细介绍 Reachy Mini Python SDK 的所有可用接口和功能。

---

## 目录

1. [核心类](#核心类)
2. [运动控制](#运动控制)
3. [摄像头控制](#摄像头控制)
4. [音频控制](#音频控制)
5. [传感器数据](#传感器数据)
6. [工具函数](#工具函数)
7. [应用开发](#应用开发)

---

## 核心类

### `ReachyMini`

Reachy Mini 机器人的主控制类，提供运动控制、媒体访问等核心功能。

#### 初始化

```python
from reachy_mini import ReachyMini

with ReachyMini(
    robot_name: str = "reachy_mini",
    connection_mode: Literal["auto", "localhost_only", "network"] = "auto",
    spawn_daemon: bool = False,
    use_sim: bool = False,
    timeout: float = 5.0,
    automatic_body_yaw: bool = True,
    log_level: str = "INFO",
    media_backend: str = "default",
) as mini:
    # 使用机器人
    pass
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `robot_name` | str | "reachy_mini" | 机器人名称 |
| `connection_mode` | str | "auto" | 连接模式："auto"(自动)、"localhost_only"(仅本地)、"network"(网络) |
| `spawn_daemon` | bool | False | 是否启动守护进程 |
| `use_sim` | bool | False | 是否使用模拟器 |
| `timeout` | float | 5.0 | 连接超时时间（秒） |
| `automatic_body_yaw` | bool | True | 是否自动计算身体偏航角 |
| `log_level` | str | "INFO" | 日志级别 |
| `media_backend` | str | "default" | 媒体后端："default"、"gstreamer"、"webrtc"、"no_media" |

---

## 运动控制

### 1. 基础姿态控制

#### `set_target()` - 立即设置目标姿态

```python
mini.set_target(
    head: Optional[np.ndarray] = None,      # 4x4 位姿矩阵
    antennas: Optional[Union[np.ndarray, List[float]]] = None,  # [右天线, 左天线] (弧度)
    body_yaw: Optional[float] = None,       # 身体偏航角 (弧度)
)
```

**说明：** 立即设置机器人到目标姿态，无插值，响应最快。

**示例：**

```python
import numpy as np
from reachy_mini.utils import create_head_pose

# 设置头部姿态 (向前 10mm, 抬头 10度)
head = create_head_pose(z=10, pitch=10, mm=True, degrees=True)
mini.set_target(head=head)

# 设置天线角度 (弧度)
mini.set_target(antennas=[0.5, -0.5])  # 右天线0.5rad, 左天线-0.5rad

# 同时设置头部、天线和身体
mini.set_target(
    head=head,
    antennas=[0.0, 0.0],
    body_yaw=0.0
)
```

#### `goto_target()` - 平滑运动到目标姿态

```python
mini.goto_target(
    head: Optional[np.ndarray] = None,
    antennas: Optional[Union[np.ndarray, List[float]]] = None,
    duration: float = 0.5,  # 运动持续时间（秒）
    method: InterpolationTechnique = InterpolationTechnique.MIN_JERK,  # 插值方法
    body_yaw: Optional[float] = None,
)
```

**插值方法：**

| 方法 | 说明 |
|------|------|
| `InterpolationTechnique.LINEAR` | 线性插值 |
| `InterpolationTechnique.MIN_JERK` | 最小加加速度（默认，最平滑） |
| `InterpolationTechnique.EASE_IN_OUT` | 缓入缓出 |
| `InterpolationTechnique.CARTOON` | 卡通效果（夸张动作） |

**示例：**

```python
from reachy_mini.utils.interpolation import InterpolationTechnique

# 平滑运动到目标位置，持续 1 秒
head = create_head_pose(x=50, roll=15, mm=True, degrees=True)
mini.goto_target(head=head, duration=1.0)

# 使用不同的插值方法
mini.goto_target(
    head=head,
    duration=2.0,
    method=InterpolationTechnique.EASE_IN_OUT
)
```

---

### 2. 视觉控制

#### `look_at_image()` - 看向图像坐标

```python
head_pose = mini.look_at_image(
    u: int,              # 图像水平坐标 (像素)
    v: int,              # 图像垂直坐标 (像素)
    duration: float = 1.0,  # 运动持续时间（秒）
    perform_movement: bool = True,  # 是否执行运动（False 仅计算）
) -> np.ndarray  # 返回计算的头部位姿 (4x4矩阵)
```

**说明：** 控制机器人头部看向摄像头画面上的指定点。

**示例：**

```python
# 看向图像中心 (假设分辨率 1920x1080)
head_pose = mini.look_at_image(960, 540, duration=0.5)

# 仅计算位姿，不执行运动
head_pose = mini.look_at_image(960, 540, perform_movement=False)
# 稍后可以手动执行
mini.set_target(head=head_pose)
```

#### `look_at_world()` - 看向世界坐标

```python
head_pose = mini.look_at_world(
    x: float,  # X坐标 (米)
    y: float,  # Y坐标 (米)
    z: float,  # Z坐标 (米)
    duration: float = 1.0,
    perform_movement: bool = True,
) -> np.ndarray
```

**坐标系说明：**
- X 轴：前方
- Y 轴：左方
- Z 轴：上方

**示例：**

```python
# 看向前方 0.3米，上方 0.1米 的点
head_pose = mini.look_at_world(x=0.3, y=0, z=0.1, duration=1.0)

# 看向左侧的点
head_pose = mini.look_at_world(x=0.2, y=0.2, z=0, duration=0.8)
```

---

### 3. 关节控制

#### `get_current_joint_positions()` - 获取当前关节位置

```python
head_joints, antennas_joints = mini.get_current_joint_positions()
# head_joints: List[float] - 7个头部关节角度 (弧度)
# antennas_joints: List[float] - 2个天线角度 (弧度)
```

#### `get_current_head_pose()` - 获取当前头部位姿

```python
head_pose = mini.get_current_head_pose()
# 返回 4x4 齐次变换矩阵
```

#### `set_target_head_pose()` - 设置头部目标位姿

```python
mini.set_target_head_pose(pose: np.ndarray)  # 4x4 位姿矩阵
```

#### `set_target_antenna_joint_positions()` - 设置天线目标角度

```python
mini.set_target_antenna_joint_positions(antennas: List[float])  # [右天线, 左天线] (弧度)
```

#### `set_target_body_yaw()` - 设置身体目标偏航角

```python
mini.set_target_body_yaw(body_yaw: float)  # 偏航角 (弧度)
```

---

### 4. 动作库

#### `play_move()` - 播放预设动作

```python
from reachy_mini.motion.recorded_move import RecordedMove

mini.play_move(
    move: Move,                          # 动作对象
    play_frequency: float = 100.0,       # 播放频率 (Hz)
    initial_goto_duration: float = 0.0,  # 初始定位时间 (秒)
    sound: bool = True,                  # 是否播放声音
)
```

#### `RecordedMove` - 录制动作

```python
from reachy_mini.motion.recorded_move import RecordedMoves, RecordedMove

# 加载 HuggingFace 动作库
moves = RecordedMoves("pollen-robotics/reachy-mini-emotions-library")

# 列出所有动作
print(moves.list_moves())

# 获取并播放特定动作
move = moves.get("happy")
mini.play_move(move)
```

**可用的动作库：**
- `pollen-robotics/reachy-mini-emotions-library` - 表情库
- `pollen-robotics/reachy-mini-dances-library` - 舞蹈库

---

### 5. 行为控制

#### `wake_up()` - 唤醒机器人

```python
mini.wake_up()
```

**说明：** 机器人移动到初始位置，播放唤醒音效和动作。

#### `goto_sleep()` - 休眠机器人

```python
mini.goto_sleep()
```

**说明：** 机器人移动到休眠位置，播放休眠音效。

---

### 6. 运动录制

#### `start_recording()` - 开始录制

```python
mini.start_recording()
```

#### `stop_recording()` - 停止录制并获取数据

```python
recorded_data = mini.stop_recording()
# 返回: List[Dict] - 包含时间戳、头部位姿、天线角度、身体偏航角
```

**示例：**

```python
# 录制动作
mini.start_recording()
time.sleep(5)  # 录制5秒
data = mini.stop_recording()

# 分析录制数据
for frame in data:
    print(f"时间: {frame['time']}")
    print(f"头部: {frame['head']}")
    print(f"天线: {frame['antennas']}")
```

---

### 7. 电机控制

#### `enable_motors()` - 启用电机

```python
mini.enable_motors(ids: Optional[List[str]] = None)
```

**有效电机名称：**
- `body_rotation` - 身体旋转
- `stewart_1` ~ `stewart_6` - 斯图尔特平台关节
- `right_antenna` - 右天线
- `left_antenna` - 左天线

**示例：**

```python
# 启用所有电机
mini.enable_motors()

# 仅启用头部电机
mini.enable_motors(ids=['body_rotation', 'stewart_1', 'stewart_2', 'stewart_3',
                        'stewart_4', 'stewart_5', 'stewart_6'])
```

#### `disable_motors()` - 禁用电机

```python
mini.disable_motors(ids: Optional[List[str]] = None)
```

#### `enable_gravity_compensation()` - 启用重力补偿

```python
mini.enable_gravity_compensation()
```

#### `disable_gravity_compensation()` - 禁用重力补偿

```python
mini.disable_gravity_compensation()
```

---

## 摄像头控制

### 访问摄像头

```python
# 通过 ReachyMini 访问
frame = mini.media.get_frame()  # 获取一帧图像

# 或直接使用 MediaManager
from reachy_mini.media.media_manager import MediaManager

media = MediaManager()
frame = media.get_frame()
media.close()
```

### 摄像头属性

```python
camera = mini.media.camera

# 获取分辨率
width, height = camera.resolution
print(f"分辨率: {width}x{height}")

# 获取帧率
fps = camera.framerate
print(f"帧率: {fps} fps")

# 获取相机内参矩阵
K = camera.K
# K = [[fx,  0, cx],
#      [ 0, fy, cy],
#      [ 0,  0,  1]]

# 获取畸变系数
D = camera.D
# D = [k1, k2, p1, p2, k3]
```

### 设置分辨率

```python
from reachy_mini.media.camera_constants import CameraResolution

# 设置摄像头分辨率
camera.set_resolution(CameraResolution.R1280x720at30fps)
```

**可用分辨率：**

| 分辨率 | 帧率 | 说明 |
|--------|------|------|
| 640x480 | 30fps | VGA |
| 1280x720 | 30fps | HD |
| 1280x720 | 60fps | HD 高帧率 |
| 1920x1080 | 30fps | Full HD |
| 1920x1080 | 60fps | Full HD 高帧率 |
| 3840x2160 | 30fps | 4K UHD |

### 摄像头标定

```python
# 获取相机标定参数
K = camera.K  # 3x3 内参矩阵
D = camera.D  # 5x1 畸变系数

# 使用 OpenCV 进行图像去畸变
import cv2
frame_undistorted = cv2.undistort(frame, K, D)
```

---

## 音频控制

### 播放声音

```python
# 播放声音文件
mini.media.play_sound("/path/to/sound.wav")

# 支持的格式: WAV, MP3 等（取决于后端）
```

### 录制音频

```python
# 开始录音
mini.media.start_recording()

# 获取音频样本
audio_sample = mini.media.get_audio_sample()
# 返回: np.ndarray[float32] - 音频数据

# 停止录音
mini.media.stop_recording()
```

### 音频参数

```python
# 获取采样率
input_samplerate = mini.media.get_input_audio_samplerate()   # 默认 16000 Hz
output_samplerate = mini.media.get_output_audio_samplerate() # 默认 16000 Hz

# 获取声道数
input_channels = mini.media.get_input_channels()   # 默认 2 (立体声)
output_channels = mini.media.get_output_channels() # 默认 2 (立体声)
```

### 音频流播放

```python
import numpy as np

# 开始播放流
mini.media.start_playing()

# 推送音频数据
audio_data = np.random.randn(1600).astype(np.float32)  # 0.1秒的音频 @ 16kHz
mini.media.push_audio_sample(audio_data)

# 停止播放
mini.media.stop_playing()
```

### 声源定位 (DoA)

```python
# 获取声源方向（需要 ReSpeaker 麦克风阵列）
doa_result = mini.media.get_DoA()

if doa_result is not None:
    angle, speech_detected = doa_result
    print(f"声源角度: {angle:.2f} 弧度 ({np.rad2deg(angle):.1f} 度)")
    print(f"检测到语音: {speech_detected}")
```

**角度说明：**
- 0 弧度：左侧
- π/2 弧度：前方/后方
- π 弧度：右侧

---

## 传感器数据

### IMU 数据（仅 Wireless 版本）

```python
# 获取 IMU 数据
imu_data = mini.imu

if imu_data is not None:
    # 加速度计 (m/s²)
    accel_x, accel_y, accel_z = imu_data['accelerometer']

    # 陀螺仪 (rad/s)
    gyro_x, gyro_y, gyro_z = imu_data['gyroscope']

    # 四元数姿态 [w, x, y, z]
    quat_w, quat_x, quat_y, quat_z = imu_data['quaternion']

    # 温度 (°C)
    temperature = imu_data['temperature']

    print(f"加速度: ({accel_x:.2f}, {accel_y:.2f}, {accel_z:.2f}) m/s²")
    print(f"角速度: ({gyro_x:.2f}, {gyro_y:.2f}, {gyro_z:.2f}) rad/s")
    print(f"温度: {temperature:.1f}°C")
```

**注意：** Lite 版本不支持 IMU，调用返回 `None`。

---

## 工具函数

### `create_head_pose()` - 创建头部位姿

```python
from reachy_mini.utils import create_head_pose

pose = create_head_pose(
    x: float = 0,           # X 位置 (米)
    y: float = 0,           # Y 位置 (米)
    z: float = 0,           # Z 位置 (米)
    roll: float = 0,        # 翻滚角
    pitch: float = 0,       # 俯仰角
    yaw: float = 0,         # 偏航角
    mm: bool = False,       # 如果 True，位置单位为毫米
    degrees: bool = True,   # 如果 True，角度单位为度
) -> np.ndarray  # 4x4 齐次变换矩阵
```

**示例：**

```python
# 创建一个向前 50mm，向上 20mm，抬头 15 度的位姿
pose = create_head_pose(x=50, z=20, pitch=15, mm=True, degrees=True)

# 创建一个使用弧度和米的位姿
pose = create_head_pose(x=0.1, yaw=0.5, mm=False, degrees=False)
```

### 插值函数

```python
from reachy_mini.utils.interpolation import (
    minimum_jerk,
    linear_pose_interpolation,
    InterpolationTechnique,
    time_trajectory
)

# 最小加加速度插值
import numpy as np
start = np.array([0.0, 0.0, 0.0])
end = np.array([1.0, 1.0, 1.0])
duration = 2.0

interpolation_func = minimum_jerk(start, end, duration)
position_at_t = interpolation_func(1.0)  # t=1秒时的位置

# 位姿线性插值
pose_start = np.eye(4)
pose_end = create_head_pose(x=0.1, yaw=0.5)
interpolated_pose = linear_pose_interpolation(pose_start, pose_end, 0.5)  # 中间位姿

# 时间轨迹（用于自定义插值方法）
t_scaled = time_trajectory(0.5, InterpolationTechnique.MIN_JERK)
```

---

## 应用开发

### `ReachyMiniApp` - 应用基类

```python
from reachy_mini.apps.app import ReachyMiniApp
from reachy_mini import ReachyMini
import threading

class MyApp(ReachyMiniApp):
    custom_app_url = "http://localhost:8080"  # 可选：Web 界面 URL
    request_media_backend = "default"         # 可选：媒体后端

    def run(self, reachy_mini: ReachyMini, stop_event: threading.Event):
        """应用主逻辑"""
        while not stop_event.is_set():
            # 你的应用逻辑
            reachy_mini.goto_target(
                head=create_head_pose(pitch=10, degrees=True),
                duration=1.0
            )
            time.sleep(2)

# 运行应用
if __name__ == "__main__":
    app = MyApp()
    app.wrapped_run()
```

### 应用管理命令

```bash
# 创建新应用
python -m reachy_mini.apps.app create my_app /path/to/app

# 检查应用
python -m reachy_mini.apps.app check /path/to/app

# 发布应用到应用商店
python -m reachy_mini.apps.app publish /path/to/app "提交信息"
```

---

## 媒体后端选择

### 可用的媒体后端

| 后端 | 说明 | 适用场景 |
|------|------|----------|
| `default` | OpenCV + SoundDevice | 跨平台默认选项 |
| `default_no_video` | 仅音频 | 无需摄像头时使用 |
| `gstreamer` | GStreamer | 高级音视频处理 |
| `gstreamer_no_video` | GStreamer 仅音频 | 高级音频处理 |
| `webrtc` | WebRTC | 远程流媒体 |
| `no_media` | 禁用媒体 | 无需音视频 |

### 使用示例

```python
# 禁用媒体（纯运动控制）
with ReachyMini(media_backend="no_media") as mini:
    mini.goto_target(head=create_head_pose(pitch=10, degrees=True))

# 使用 GStreamer
with ReachyMini(media_backend="gstreamer") as mini:
    frame = mini.media.get_frame()

# 使用 WebRTC（远程连接）
with ReachyMini(media_backend="webrtc") as mini:
    frame = mini.media.get_frame()
```

---

## 完整示例

### 示例 1：基础运动控制

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import time

with ReachyMini() as mini:
    # 唤醒
    mini.wake_up()
    time.sleep(2)

    # 向前看
    pose = create_head_pose(z=50, mm=True)
    mini.goto_target(head=pose, duration=1.0)
    time.sleep(1)

    # 向左看
    pose = create_head_pose(yaw=30, degrees=True)
    mini.goto_target(head=pose, duration=1.0)
    time.sleep(1)

    # 向右看
    pose = create_head_pose(yaw=-30, degrees=True)
    mini.goto_target(head=pose, duration=1.0)
    time.sleep(1)

    # 回到中心
    pose = create_head_pose()
    mini.goto_target(head=pose, duration=1.0)

    # 休眠
    time.sleep(1)
    mini.goto_sleep()
```

### 示例 2：摄像头追踪

```python
from reachy_mini import ReachyMini
import cv2

with ReachyMini() as mini:
    while True:
        # 获取摄像头画面
        frame = mini.media.get_frame()
        if frame is None:
            break

        # 显示画面
        cv2.imshow('Reachy Mini Camera', frame)

        # 等待鼠标点击
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):  # 空格键
            # 看向画面中心
            h, w = frame.shape[:2]
            mini.look_at_image(w//2, h//2, duration=0.5)

    cv2.destroyAllWindows()
```

### 示例 3：语音定位响应

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import time

with ReachyMini(media_backend="default") as mini:
    print("声源定位演示开始...")

    while True:
        # 获取声源方向
        doa_result = mini.media.get_DoA()

        if doa_result is not None:
            angle, speech_detected = doa_result

            if speech_detected:
                print(f"检测到语音！方向: {np.rad2deg(angle):.1f}°")

                # 转向声源方向
                # DoA 角度: 0=左, π/2=前, π=右
                # 机器人偏航: 正值=左转, 负值=右转
                robot_yaw = (np.pi/2 - angle)

                pose = create_head_pose(yaw=np.rad2deg(robot_yaw), degrees=True)
                mini.goto_target(head=pose, duration=0.5)

        time.sleep(0.1)
```

### 示例 4：动作录制与回放

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import time

with ReachyMini() as mini:
    print("准备录制动作...")
    print("按 Enter 开始录制...")
    input()

    # 开始录制
    mini.start_recording()
    print("录制中... 5秒")

    # 在录制期间执行一些动作
    mini.goto_target(create_head_pose(pitch=20, degrees=True), duration=1.0)
    time.sleep(1)
    mini.goto_target(create_head_pose(yaw=30, degrees=True), duration=1.0)
    time.sleep(1)
    mini.goto_target(create_head_pose(yaw=-30, degrees=True), duration=1.0)
    time.sleep(2)

    # 停止录制
    recorded_data = mini.stop_recording()
    print(f"录制完成！共 {len(recorded_data)} 帧")

    # 回放录制的动作
    print("回放动作...")
    for frame in recorded_data:
        head = frame['head']
        antennas = frame['antennas']
        mini.set_target(head=head, antennas=antennas)
        time.sleep(0.01)  # 维持原始帧率
```

---

## 注意事项

1. **连接模式：**
   - 本地机器人：使用 `connection_mode="localhost_only"`
   - 远程机器人：使用 `connection_mode="network"`
   - 自动检测：使用 `connection_mode="auto"`（默认）

2. **坐标系：**
   - 位置单位：默认为米，可使用 `mm=True` 切换到毫米
   - 角度单位：默认为度，可使用 `degrees=False` 切换到弧度
   - 坐标方向：X=前，Y=左，Z=上

3. **运动限制：**
   - 头部运动范围有限，避免超出关节限制
   - 使用平滑运动 (`goto_target`) 以获得更好的效果
   - 避免快速连续的运动命令

4. **媒体后端：**
   - Lite 版本推荐使用 `default` 后端
   - Wireless 版本本地连接使用 `gstreamer`
   - Wireless 版本远程连接使用 `webrtc`

5. **错误处理：**
   - 使用 `try-except` 捕获连接错误
   - 检查返回值（如摄像头帧可能为 `None`）
   - 使用上下文管理器 (`with`) 确保资源正确释放

---

## 更多资源

- [官方文档](https://pollen-robotics.github.io/reachy-mini/)
- [API 参考](https://pollen-robotics.github.io/reachy-mini/api/)
- [示例代码](https://github.com/pollen-robotics/reachy-mini)
