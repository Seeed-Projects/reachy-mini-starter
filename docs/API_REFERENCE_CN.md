# Reachy Mini API 接口开发指南

完整的 Reachy Mini 机器人控制接口文档，涵盖所有参数范围、可控制自由度和使用限制。

---

## 📋 接口概览与 Demo 映射

| 接口类型 | 延迟 | 适用场景 | 已实现 Demo | 状态 |
|---------|------|---------|------------|------|
| **REST API** | 20-50ms | 单次命令、配置查询 | ✅ 全部实现 | 完成 |
| **WebSocket** | <10ms | 实时控制、状态流 | ⏳ 待实现 | 计划中 |
| **Zenoh** | 10-20ms | Python SDK 开发 | ⏳ 待实现 | 计划中 |
| **BLE** | 100-500ms | 配置调试 | ⏳ 待实现 | 计划中 |

### 🎯 REST API Demo 覆盖情况

| API 端点类别 | 功能 | Demo 文件 | 状态 |
|-------------|------|----------|------|
| `/move/goto` | 运动控制 | [`02_basic_body_rotation`](../demos/02_basic_body_rotation/test_body_rotation.py) | ✅ |
| `/move/goto` | 点头动作 | [`03_basic_nod_head`](../demos/03_basic_nod_head/test_nod_head.py) | ✅ |
| `/move/goto` | 摇头动作 | [`04_basic_shake_head`](../demos/04_basic_shake_head/test_shake_head.py) | ✅ |
| `/volume/*` | 音频控制 | [`01_basic_audio_control`](../demos/01_basic_audio_control/test_audio_control.py) | ✅ |
| `/motors/*` | 电机控制 | 各运动 Demo 中使用 | ✅ |

---

## 目录

1. [REST API 接口](#1-rest-api-接口)
2. [WebSocket 接口](#2-websocket-接口)
3. [Zenoh 协议接口](#3-zenoh-协议接口)
4. [BLE 蓝牙接口](#4-ble-蓝牙接口)
5. [附录](#5-附录)

---

## 1. REST API 接口

**基础 URL**: `http://192.168.137.225:8000`

**特点**: 基于 HTTP 的请求-响应模式，适用于单次命令、配置查询，延迟 20-50ms

### 1.1 运动控制 `/move`

#### 可控对象与参数范围

| 可控对象 | 参数 | 范围 | 单位 | 说明 |
|---------|-----|------|------|------|
| **头部姿态** | x | ±0.05 | 米 | 前后位置，向前为正 |
| | y | ±0.05 | 米 | 左右位置，向左为正 |
| | z | -0.03 ~ +0.08 | 米 | 上下位置，向上为正 |
| | roll | ±25 | 度 | 翻滚角，右倾为正 |
| | pitch | ±35 | 度 | 俯仰角，抬头为正 |
| | yaw | ±160 | 度 | 偏航角，左转为正 |
| **天线** | antennas[0] | -80 ~ +80 | 度 | 左天线角度 |
| | antennas[1] | -80 ~ +80 | 度 | 右天线角度 |
| **身体** | body_yaw | -160 ~ +160 | 度 | 身体偏航角 |
| **运动参数** | duration | 0.1 ~ 10.0 | 秒 | 运动时长 |

**插值方式**:
| 方式 | 说明 |
|-----|------|
| `linear` | 线性插值，匀速运动 |
| `minjerk` | 最小抖动插值，平滑运动（推荐） |
| `ease` | 缓动插值，加减速平滑 |
| `cartoon` | 卡通插值，弹性效果 |

#### 接口列表

**POST `/move/goto`** - 平滑运动到目标（支持插值）

> 📁 **Demo**: [身体旋转](../demos/02_basic_body_rotation/test_body_rotation.py) | [点头](../demos/03_basic_nod_head/test_nod_head.py) | [摇头](../demos/04_basic_shake_head/test_shake_head.py)

请求体示例:
```json
{
  "head_pose": {"x": 0, "y": 0, "z": 0.05, "roll": 0, "pitch": 15, "yaw": 0},
  "antennas": [30, -30],
  "body_yaw": 0,
  "duration": 2.0,
  "interpolation": "minjerk"
}
```

响应:
```json
{"uuid": "123e4567-e89b-12d3-a456-426614174000"}
```

---

**POST `/move/set_target`** - 立即设置目标（无轨迹）

请求体示例:
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

**POST `/move/goto_joint_positions`** - 关节空间运动

| 可控对象 | 参数 | 范围 | 单位 | 说明 |
|---------|-----|------|------|------|
| **头部关节** | head_joint_positions[0] | ±2.79 | 弧度 | yaw_body (-160°~+160°) |
| | head_joint_positions[1] | -0.84 ~ +1.40 | 弧度 | roll_sp_1 (-48°~+80°) |
| | head_joint_positions[2] | -0.84 ~ +1.40 | 弧度 | roll_sp_2 (-48°~+80°) |
| | head_joint_positions[3] | -0.84 ~ +1.40 | 弧度 | roll_sp_3 (-48°~+80°) |
| | head_joint_positions[4] | -1.22 ~ +1.40 | 弧度 | pitch_sp_1 (-70°~+80°) |
| | head_joint_positions[5] | -0.84 ~ +1.40 | 弧度 | pitch_sp_2 (-48°~+80°) |
| | head_joint_positions[6] | -1.22 ~ +1.40 | 弧度 | pitch_sp_3 (-70°~+80°) |
| **天线关节** | antennas_joint_positions[0] | ±1.40 | 弧度 | 左天线 (-80°~+80°) |
| | antennas_joint_positions[1] | ±1.40 | 弧度 | 右天线 (-80°~+80°) |

---

**POST `/move/play/wake_up`** - 唤醒动画

**POST `/move/play/goto_sleep`** - 休眠动画

**POST `/move/play/recorded-move-dataset/{dataset}/{move}`** - 播放预设动作
- 示例: `/move/play/recorded-move-dataset/pollen-robotics/reachy-mini-dances-library/another_one_bites_the_dust`

**GET `/move/running`** - 获取运行中的运动

**POST `/move/stop`** - 停止运动

---

### 1.2 状态查询 `/state`

#### 可查询对象

| 查询对象 | 接口 | 返回数据 | 值域 |
|---------|-----|---------|------|
| **头部姿态** | GET `/state/present_head_pose` | x, y, z, roll, pitch, yaw | 见 1.1 节范围 |
| **身体偏航** | GET `/state/present_body_yaw` | 弧度值 | -2.79 ~ +2.79 |
| **天线位置** | GET `/state/present_antenna_joint_positions` | [左, 右] 弧度 | ±1.40 |
| **完整状态** | GET `/state/full` | 所有状态 | - |

**GET `/state/full` 查询参数**:
| 参数 | 默认值 | 说明 |
|-----|-------|------|
| with_control_mode | true | 控制模式 |
| with_head_pose | true | 当前头部姿态 |
| with_target_head_pose | false | 目标头部姿态 |
| with_head_joints | false | 头部关节角度 |
| with_target_head_joints | false | 目标关节角度 |
| with_body_yaw | true | 身体偏航 |
| with_target_body_yaw | false | 目标身体偏航 |
| with_antenna_positions | true | 天线位置 |
| with_target_antenna_positions | false | 目标天线位置 |
| with_passive_joints | false | 被动关节 |
| use_pose_matrix | false | 使用矩阵格式 |

---

### 1.3 电机控制 `/motors`

> 📁 **Demo**: 所有运动 Demo 中使用

#### 可控对象

| 控制对象 | 参数 | 说明 |
|---------|-----|------|
| **电机模式** | `enabled` | 电机启用，刚性控制（mode 3） |
| | `disabled` | 电机禁用，可手动移动（mode 0） |
| | `gravity_compensation` | 重力补偿，保持姿态（mode 5） |

**接口列表**:
- **GET `/motors/status`** - 获取电机状态
- **POST `/motors/set_mode/{mode}`** - 设置电机模式

---

### 1.4 音频控制 `/volume`

> 📁 **Demo**: [音频控制](../demos/01_basic_audio_control/test_audio_control.py)

#### 可控对象与参数范围

| 可控对象 | 参数 | 范围 | 默认值 | 单位 |
|---------|-----|------|-------|------|
| **音量** | volume | 0 ~ 100 | 50 | % |
| **麦克风音量** | volume | 0 ~ 100 | 50 | % |
| **采样率** | sample_rate | 16000 | - | Hz |
| **通道数** | channels | 2 | - | - |
| **声源方向** | doa_angle | 0 ~ π | - | 弧度 |

**声源方向说明**:
| 弧度 | 方向 |
|-----|------|
| 0 | 左边 |
| π/2 | 前方/后方 |
| π | 右边 |

#### 接口列表

**GET `/volume/current`** - 获取扬声器音量

> ✅ **已在 Demo 中实现**

响应:
```json
{"volume": 50, "device": "reachy_mini_audio", "platform": "Linux"}
```

**POST `/volume/set`** - 设置扬声器音量

> ✅ **已在 Demo 中实现**

请求体:
```json
{"volume": 75}
```

响应:
```json
{"volume": 75, "device": "reachy_mini_audio", "platform": "Linux"}
```

**POST `/volume/test-sound`** - 播放测试音

> ✅ **已在 Demo 中实现**

响应:
```json
{"status": "ok", "message": "Test sound played"}
```

**GET `/volume/microphone/current`** - 获取麦克风增益

> ✅ **已在 Demo 中实现**

响应:
```json
{"volume": 60, "device": "reachy_mini_audio", "platform": "Linux"}
```

**POST `/volume/microphone/set`** - 设置麦克风增益

> ✅ **已在 Demo 中实现**

请求体:
```json
{"volume": 80}
```

---

### 1.5 应用管理 `/apps`

| 接口 | 方法 | 说明 | 状态 |
|-----|------|------|------|
| `/apps/list-available` | GET | 列出可用应用 | ⏳ 待实现 |
| `/apps/install` | POST | 安装应用 | ⏳ 待实现 |
| `/apps/start-app/{app_name}` | POST | 启动应用 | ⏳ 待实现 |
| `/apps/stop-current-app` | POST | 停止应用 | ⏳ 待实现 |
| `/apps/current-app-status` | GET | 获取应用状态 | ⏳ 待实现 |

**安装应用请求示例**:
```json
{"source": "huggingface", "app_id": "pollen-robotics/reachy_mini_conversation_app"}
```

---

### 1.6 运动学 `/kinematics`

| 引擎类型 | 说明 |
|---------|------|
| `AnalyticalKinematics` | 解析解（默认，最快） |
| `PlacoKinematics` | 优化解（支持碰撞检测） |
| `NNKinematics` | 神经网络（需要模型） |

| 接口 | 方法 | 说明 | 状态 |
|-----|------|------|------|
| `/kinematics/info` | GET | 获取运动学信息 | ⏳ 待实现 |
| `/kinematics/urdf` | GET | 获取 URDF 模型 | ⏳ 待实现 |
| `/kinematics/stl/{filename}` | GET | 获取 STL 文件（3D 可视化） | ⏳ 待实现 |

---

### 1.7 守护进程 `/daemon`

| 接口 | 方法 | 说明 | 状态 |
|-----|------|------|------|
| `/daemon/start` | POST | 启动守护进程 | ⏳ 待实现 |
| `/daemon/stop` | POST | 停止守护进程 | ⏳ 待实现 |
| `/daemon/restart` | POST | 重启守护进程 | ⏳ 待实现 |
| `/daemon/status` | GET | 获取状态 | ⏳ 待实现 |

---

## 2. WebSocket 接口

**特点**: 双向实时通信，延迟 <10ms，支持 60Hz+ 高频控制

**状态**: ⏳ **待实现 Demo**

### 2.1 实时控制 `/move/ws/set_target`

**连接**: `ws://192.168.137.225:8000/move/ws/set_target`

#### 可控对象与参数范围

| 可控对象 | 参数 | 范围 | 单位 | 说明 |
|---------|-----|------|------|------|
| **头部姿态** | position.x | ±0.05 | 米 | 前后位置 |
| | position.y | ±0.05 | 米 | 左右位置 |
| | position.z | -0.03 ~ +0.08 | 米 | 上下位置 |
| | rotation (四元数) | 单位四元数 | - | 姿态 |
| **天线** | target_antennas[0] | -80 ~ +80 | 度 | 左天线 |
| | target_antennas[1] | -80 ~ +80 | 度 | 右天线 |
| **身体** | target_body_yaw | -160 ~ +160 | 度 | 身体偏航 |

**发送消息格式**（60Hz+）:
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

**接收错误反馈**:
```json
{"status": "error", "detail": "error message"}
```

---

### 2.2 状态流 `/state/ws/full`

**连接**: `ws://192.168.137.225:8000/state/ws/full?frequency=30`

#### 查询参数与可控范围

| 参数 | 范围 | 默认值 | 说明 |
|-----|------|-------|------|
| frequency | 1 ~ 100 | 10 | 更新频率（Hz） |
| with_head_pose | true/false | true | 包含头部姿态 |
| with_head_joints | true/false | false | 包含关节角度 |
| with_antenna_positions | true/false | true | 包含天线位置 |
| use_pose_matrix | true/false | false | 使用矩阵格式 |

**接收消息**（持续流）:
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

### 2.3 运动更新 `/move/ws/updates`

**连接**: `ws://192.168.137.225:8000/move/ws/updates`

#### 事件类型

| 事件类型 | 说明 |
|---------|------|
| `move_started` | 运动开始 |
| `move_completed` | 运动完成 |
| `move_failed` | 运动失败 |
| `move_cancelled` | 运动取消 |

**接收事件**:
```json
{
  "type": "move_started",
  "uuid": "123e4567-e89b-12d3-a456-426614174000",
  "details": ""
}
```

---

## 3. Zenoh 协议接口

**特点**: SDK 主要通信方式，延迟 10-20ms，高带宽，支持高频控制

**状态**: ⏳ **待实现 Demo**

### 3.1 连接配置

**客户端模式（指定 IP）**:
```python
{"mode": "client", "connect": {"endpoints": ["tcp/192.168.137.225:7447"]}}
```

**对等模式（自动发现）**:
```python
{"mode": "peer", "scouting": {"multicast": {"enabled": true}}}
```

---

### 3.2 Topic 与可控对象

| Topic | 方向 | 可控/返回对象 | 数据类型 |
|-------|------|--------------|---------|
| `reachy_mini/command` | → | 头部姿态、天线、身体偏航、电机模式 | dict |
| `reachy_mini/joint_positions` | ← | 所有 9 个关节位置 | list |
| `reachy_mini/head_pose` | ← | 头部 4x4 姿态矩阵 | ndarray |
| `reachy_mini/daemon_status` | ← | 守护进程状态 | dict |
| `reachy_mini/task` | → | 任务请求 | dict |
| `reachy_mini/task_progress` | ← | 任务进度 | dict |
| `reachy_mini/recorded_data` | ← | 录制数据 | bytes |

---

### 3.3 命令格式与参数范围

#### 发送命令到 `reachy_mini/command`

**设置目标姿态**:
```python
{
    "head_pose": [[4x4 矩阵]],  # 头部姿态矩阵
    "antennas_joint_positions": [0.5, -0.5],  # 天线弧度 [-1.40, +1.40]
    "body_yaw": 0.0  # 身体偏航 弧度 [-2.79, +2.79]
}
```

**启用扭矩**:
```python
{"torque": True}
```

**启用重力补偿**:
```python
{"gravity_compensation": True}
```

---

### 3.4 返回数据格式

**关节位置** (`reachy_mini/joint_positions`):
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

## 4. BLE 蓝牙接口

**特点**: 近距离配置、调试、应急控制，延迟 100-500ms

**状态**: ⏳ **待实现 Demo**

### 4.1 连接信息

| 项目 | 值 |
|-----|-----|
| **BLE 设备名称** | ReachyMini |
| **PIN 码获取** | 序列号后 5 位（`dfu-util -l` 查询） |

### 4.2 使用 nRF Connect 连接

1. 安装 nRF Connect (Android/iOS)
2. 扫描并连接 "ReachyMini" 设备
3. Unknown Service → WRITE 发送十六进制命令

### 4.3 可控命令与参数

| 命令 | 十六进制 | 说明 | 状态 |
|-----|---------|------|------|
| **PIN 验证** | `50494E5F3030303033` | PIN_00033（替换为实际 PIN） | ⏳ 待实现 |
| **查询状态** | `535441545553` | STATUS | ⏳ 待实现 |
| **重置热点** | `434D445F484F5453504F54` | CMD_HOTSPOT | ⏳ 待实现 |
| **重启守护进程** | `434D445F524553544152545F4441454D4F4E` | CMD_RESTART_DAEMON | ⏳ 待实现 |
| **软件复位** | `434D445F534F4654574152455F5245534554` | CMD_SOFTWARE_RESET | ⏳ 待实现 |

### 4.4 Web Bluetooth 工具

官方工具: https://pollen-robotics.github.io/reachy_mini/

支持 Chrome 内核浏览器，可直接通过网页连接蓝牙。

---

## 5. 附录

### 5.1 机器人自由度总览

| 部位 | 自由度数 | 关节名称 | 范围（度） | 范围（弧度） |
|-----|---------|---------|-----------|-------------|
| **头部** | 7 | yaw_body | ±160° | ±2.79 |
| | | roll_sp_1/2/3 | -48° ~ +80° | -0.84 ~ +1.40 |
| | | pitch_sp_1/2/3 | -70° ~ +80° | -1.22 ~ +1.40 |
| **天线** | 2 | 左天线 | ±80° | ±1.40 |
| | | 右天线 | ±80° | ±1.40 |
| **身体** | 1 | body_yaw | ±160° | ±2.79 |

**总计**: 10 个可控自由度

### 5.2 任务空间工作空间

| 轴 | 范围 | 单位 | 说明 |
|----|------|------|------|
| X（前后） | ±0.05 | 米 | 向前为正 |
| Y（左右） | ±0.05 | 米 | 向左为正 |
| Z（上下） | -0.03 ~ +0.08 | 米 | 向上为正 |
| Roll（翻滚） | ±25 | 度 | 右倾为正 |
| Pitch（俯仰） | ±35 | 度 | 抬头为正 |
| Yaw（偏航） | ±160 | 度 | 左转为正 |

### 5.3 使用场景推荐

| 场景 | 推荐接口 | 理由 |
|-----|---------|------|
| **实时跟踪控制** | WebSocket `/move/ws/set_target` | 60Hz+，低延迟 |
| **状态监控** | WebSocket `/state/ws/full` | 可调频率，完整数据 |
| **单次运动** | REST `/move/goto` | 简单可靠 |
| **Python 开发** | Zenoh SDK | 官方支持 |
| **Web 应用** | REST + WebSocket | 浏览器兼容 |
| **移动应用** | REST API | 标准 HTTP |
| **配置调试** | BLE | 近距离配置 |

### 5.4 姿态表示格式

#### 欧拉角格式（度）
```json
{"x": 0.0, "y": 0.0, "z": 0.0, "roll": 0.0, "pitch": 0.0, "yaw": 0.0}
```

#### 四元数格式
```json
{"position": {"x": 0.0, "y": 0.0, "z": 0.0}, "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}}
```

#### 4x4 矩阵格式（扁平化）
```json
{"m": [r11, r12, r13, x, r21, r22, r23, y, r31, r32, r33, z, 0, 0, 0, 1]}
```

### 5.5 注意事项

1. **坐标系**: 右手坐标系，X 轴向前，Z 轴向上
2. **角度单位**: API 使用度，内部使用弧度
3. **安全限制**: 所有关节都有软件/硬件限位保护
4. **电机保护**: 避免长时间在极限位置
5. **网络延迟**: WebSocket <10ms，REST 20-50ms
6. **控制频率**: 建议不超过 60Hz，避免命令拥塞
7. **优先级**: 运动中的 goto 命令会被忽略（需先 stop）

---

## 示例代码

### JavaScript 实时控制

```javascript
const controlWS = new WebSocket('ws://192.168.137.225:8000/move/ws/set_target');
const stateWS = new WebSocket('ws://192.168.137.225:8000/state/ws/full?frequency=60');

// 实时控制（60Hz）
function setHeadPose(x, y, z, roll, pitch, yaw) {
  const command = {
    target_head_pose: {
      position: { x, y, z },
      rotation: eulerToQuaternion(roll, pitch, yaw)
    }
  };
  controlWS.send(JSON.stringify(command));
}

// 状态回调
stateWS.onmessage = (event) => {
  const state = JSON.parse(event.data);
  console.log('头部位置:', state.head_pose);
};
```

### Python 平滑运动

```python
import requests

# 平滑运动到目标
data = {
    "head_pose": {"x": 0, "y": 0, "z": 0.05, "roll": 0, "pitch": 15, "yaw": 0},
    "antennas": [30, -30],
    "body_yaw": 0,
    "duration": 2.0,
    "interpolation": "minjerk"
}
response = requests.post('http://192.168.137.225:8000/move/goto', json=data)
print(f"运动 UUID: {response.json()['uuid']}")
```

### Python 状态查询

```python
import requests

response = requests.get('http://192.168.137.225:8000/state/full')
state = response.json()

print(f"头部姿态: {state['head_pose']}")
print(f"天线位置: {state['antennas_position']}")
print(f"控制模式: {state['control_mode']}")
```

### Python 音频控制 (REST API)

> 📁 **Demo**: [音频控制](../demos/01_basic_audio_control/test_audio_control.py)

```python
import requests

base_url = "http://192.168.137.225:8000"

# 获取当前音量
response = requests.get(f"{base_url}/volume/current")
print(f"音量: {response.json()['volume']}%")

# 设置音量
requests.post(f"{base_url}/volume/set", json={"volume": 80})

# 播放测试音
requests.post(f"{base_url}/volume/test-sound")

# 获取麦克风增益
response = requests.get(f"{base_url}/volume/microphone/current")
print(f"麦克风增益: {response.json()['volume']}%")

# 设置麦克风增益
requests.post(f"{base_url}/volume/microphone/set", json={"volume": 70})
```

### Python 音频控制 (SDK)

```python
from reachy_mini import ReachyMini

# 初始化机器人
robot = ReachyMini()

# ===== 音频播放 =====

# 播放音频文件
robot.media.play_sound("wake_up.wav")

# 音频流播放
robot.media.start_playing()
import numpy as np
# 生成或加载音频数据 (float32, -1.0 到 1.0)
audio_data = np.random.uniform(-0.5, 0.5, 16000).astype(np.float32)
robot.media.push_audio_sample(audio_data)
robot.media.stop_playing()

# 获取音频输出参数
sample_rate = robot.media.get_output_audio_samplerate()  # 16000 Hz
channels = robot.media.get_output_channels()             # 2 (立体声)

# ===== 音频录制 =====

# 开始录音
robot.media.start_recording()

# 获取音频样本
audio_sample = robot.media.get_audio_sample()  # 返回 numpy 数组或 bytes
if audio_sample is not None:
    print(f"采样到 {len(audio_sample)} 个音频点")

# 停止录音
robot.media.stop_recording()

# 获取音频输入参数
input_sample_rate = robot.media.get_input_audio_samplerate()  # 16000 Hz
input_channels = robot.media.get_input_channels()             # 2 (立体声)

# ===== 声源方向检测 =====

# 获取声源方向
doa_result = robot.media.audio.get_DoA()
if doa_result:
    angle_radians, speech_detected = doa_result
    angle_degrees = angle_radians * 180 / 3.14159
    print(f"声源方向: {angle_degrees:.1f}°")
    print(f"检测到语音: {speech_detected}")

# ===== 低层硬件控制 =====

from reachy_mini.media.audio_control_utils import init_respeaker_usb

# 初始化 ReSpeaker 设备
respeaker = init_respeaker_usb()

if respeaker:
    # 读取麦克风增益
    mic_gain = respeaker.read("AUDIO_MGR_MIC_GAIN")
    print(f"麦克风增益: {mic_gain}")

    # 设置麦克风增益 (float 值)
    respeaker.write("AUDIO_MGR_MIC_GAIN", [2.5])

    # LED 控制
    respeaker.write("LED_BRIGHTNESS", [80])           # 亮度 0-100
    respeaker.write("LED_COLOR", [0xFF0000])          # RGB 红色
    respeaker.write("LED_EFFECT", [1])                # 效果模式

    # 读取固件版本
    version = respeaker.read("VERSION")
    print(f"固件版本: {version}")
```

### Python 录音与保存示例

```python
from reachy_mini import ReachyMini
import numpy as np
import wave

robot = ReachyMini()

# 开始录音
robot.media.start_recording()
print("正在录音...")

# 录制 5 秒
import time
sample_rate = robot.media.get_input_audio_samplerate()
duration = 5  # 秒
all_samples = []

start_time = time.time()
while time.time() - start_time < duration:
    sample = robot.media.get_audio_sample()
    if sample is not None:
        all_samples.append(sample)
    time.sleep(0.01)

robot.media.stop_recording()
print("录音完成")

# 保存为 WAV 文件
if all_samples:
    audio_array = np.concatenate(all_samples)

    # 转换为 int16 PCM
    audio_int16 = (audio_array * 32767).astype(np.int16)

    with wave.open("recording.wav", "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

    print("已保存为 recording.wav")
```

### Python TTS 语音合成示例

```python
from reachy_mini import ReachyMini
import numpy as np

robot = ReachyMini()

# 使用 pyttsx3 离线 TTS (需要安装: pip install pyttsx3)
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 150)    # 语速
engine.setProperty('volume', 0.9)  # 音量

# 保存语音到文件并播放
engine.save_to_file('你好，我是 Reachy Mini！', 'hello.wav')
engine.runAndWait()

# 播放
robot.media.play_sound("hello.wav")
```

### Python WebSocket 音频流

```python
from reachy_mini.io.audio_ws import AsyncWebSocketAudioStreamer
import numpy as np

# 连接到音频流服务器
streamer = AsyncWebSocketAudioStreamer(
    "ws://192.168.137.225:8765/audio",
    keep_alive_interval=2.0
)

# 发送音频 (支持 bytes, int16 或 float32)
audio_chunk = np.random.uniform(-0.3, 0.3, 2048).astype(np.float32)
streamer.send_audio_chunk(audio_chunk)

# 接收音频
while True:
    received_audio = streamer.get_audio_chunk(timeout=0.1)
    if received_audio is not None:
        print(f"收到音频: {len(received_audio)} 采样点")
        # 处理接收到的音频...

# 关闭连接
streamer.close()
```
