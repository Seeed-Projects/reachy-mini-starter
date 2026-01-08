# Demo 15: Reachy Mini 实时控制上位机 (WebSocket)

通过浏览器拖动滑条实时控制 Reachy Mini 机器人，使用 WebSocket 实现超低延迟控制。

## 功能特性

### 完整的运动控制

| 控制类别 | 参数 | 范围 | 单位 | 说明 |
|---------|-----|------|------|------|
| **头部位置** | X | ±0.05 | 米 | 前后位置，向前为正 |
| | Y | ±0.05 | 米 | 左右位置，向左为正 |
| | Z | -0.03 ~ +0.08 | 米 | 上下位置，向上为正 |
| **头部姿态** | Roll | ±25 | 度 | 翻滚角，右倾为正 |
| | Pitch | ±35 | 度 | 俯仰角，抬头为正 |
| | Yaw | ±160 | 度 | 偏航角，左转为正 |
| **天线** | 左天线 | ±80 | 度 | 左天线角度 |
| | 右天线 | ±80 | 度 | 右天线角度 |
| **身体** | Body Yaw | ±160 | 度 | 身体偏航角 |

### WebSocket 实时控制

- **超低延迟**: <10ms（HTTP 20-50ms）
- **持续连接**: 避免每次请求的建立开销
- **高频更新**: 支持 10/30/60Hz 控制频率
- **平滑运动**: 定时循环发送当前状态
- **自动重连**: 断线后 5 秒自动重连

### 其他功能

- 实时延迟显示
- 电机启用/禁用控制
- 一键全部回零
- WebSocket 连接状态显示

## 安装依赖

```bash
pip install flask
```

## 运行方法

1. 确保 `config.yaml` 中配置了正确的机器人 IP 地址

2. 启动服务器:
```bash
python server.py
```

3. 在浏览器中访问:
   - 本地访问: http://localhost:5000
   - 局域网访问: http://<本机IP>:5000

4. 页面会自动通过 WebSocket 连接到机器人

## 使用说明

### 控制面板

控制面板分为 4 个卡片：

1. **头部位置 (米)**
   - X 轴: 控制头部前后移动
   - Y 轴: 控制头部左右移动
   - Z 轴: 控制头部上下移动

2. **头部姿态 (度)**
   - Roll: 控制头部左右倾斜
   - Pitch: 控制头部俯仰（点头）
   - Yaw: 控制头部左右转动

3. **天线角度 (度)**
   - 左天线: 控制左天线角度
   - 右天线: 控制右天线角度

4. **身体偏航 (度)**
   - Body Yaw: 控制机器人底座旋转

### 操作步骤

1. 打开浏览器访问控制页面
2. 等待 WebSocket 自动连接（状态显示"已连接"）
3. 点击"启用电机"按钮
4. 选择更新频率（10/30/60 Hz）
5. 拖动滑条实时控制机器人运动
6. 观察延迟显示（通常 <5ms）

### 更新频率说明

| 频率 | 间隔 | 适用场景 |
|------|------|---------|
| **10 Hz** | 100ms | 平滑控制，推荐大多数场景 |
| **30 Hz** | 33ms | 快速响应，默认选项 |
| **60 Hz** | 极速响应，高精度控制 |

## 技术架构

### 架构设计

```
浏览器 ─────────[WebSocket]────────> Reachy Mini
页面服务                            WebSocket API
 :5000                               :8000/move/ws/set_target
 (Flask, 只服务静态文件)             (低延迟实时控制)
```

### WebSocket vs HTTP

| 特性 | WebSocket | HTTP |
|------|-----------|-----|
| **延迟** | <10ms | 20-50ms |
| **连接** | 持续连接 | 每次请求建立新连接 |
| **开销** | 极低 | 较高（握手、头部等） |
| **实时性** | 双向实时 | 请求-响应 |
| **平滑度** | 非常平滑 | 可能有跳跃感 |

### 为什么使用 WebSocket？

1. **低延迟**: WebSocket 建立连接后，数据传输延迟极低
2. **持续连接**: 避免 HTTP 每次请求的握手开销
3. **高频更新**: 支持定时循环发送控制命令（60Hz）
4. **平滑运动**: 持续发送当前位置，机器人平滑跟随

### 后端 (server.py)

- **Flask**: 仅提供静态文件服务
- 不做任何代理转发
- 前端直接连机器人 WebSocket

### 前端 (templates/index.html)

- **原生 WebSocket API**: 浏览器内置，无需库
- **定时循环**: 按设定频率持续发送状态
- **欧拉角转四元数**: JavaScript 实现
- **自动重连**: 断线后自动尝试重连

### WebSocket 协议

**连接地址**:
```
ws://<机器人IP>:8000/move/ws/set_target
```

**发送消息格式**:
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

## 相关 Demo

- [Demo 02: 底座旋转](../02_basic_body_rotation/) - 底座旋转基础示例
- [Demo 03: 点头动作](../03_basic_nod_head/) - 头部俯仰控制示例
- [Demo 04: 摇头动作](../04_basic_shake_head/) - 头部偏航控制示例
- [API 参考文档](../../docs/API_REFERENCE_CN.md) - 完整 API 文档（含 WebSocket）

## ⚠️ 重要开发注意事项

### API 单位问题（文档与实际不符）

**核心发现**: `/move/goto` REST API 的角度参数实际使用 **弧度 (radians)**，而非文档中标注的度数 (degrees)。

| 参数 | 文档标注 | 实际单位 | 转换关系 |
|------|---------|---------|---------|
| `head_pose.roll` | 度 | **弧度** | × π/180 |
| `head_pose.pitch` | 度 | **弧度** | × π/180 |
| `head_pose.yaw` | 度 | **弧度** | × π/180 |
| `antennas[]` | 度 | **弧度** | × π/180 |
| `body_yaw` | 度 | **弧度** | × π/180 |

**示例对比**:
```python
# 错误：直接使用度数（来自文档）
requests.post(f"{base_url}/move/goto", json={
    "body_yaw": 30,  # ❌ 会被当成 30 弧度 ≈ 1719°
    "head_pose": {"roll": 15, "pitch": 10},  # ❌ 错误
    "antennas": [45, -45]  # ❌ 错误
})

# 正确：转换为弧度
import math
requests.post(f"{base_url}/move/goto", json={
    "body_yaw": math.radians(30),  # ✅ 0.524 弧度 ≈ 30°
    "head_pose": {
        "roll": math.radians(15),   # ✅ 0.262 弧度
        "pitch": math.radians(10)   # ✅ 0.175 弧度
    },
    "antennas": [math.radians(45), math.radians(-45)]  # ✅ [0.785, -0.785]
})
```

### 验证方法

参考 [Demo 06: Zenoh 基础控制](../06_zenoh_basic_control/)，它使用正确的弧度值：
```python
# Demo 06 中的正确用法
cmd_antennas = {"antennas_joint_positions": [0.5, -0.5]}  # 弧度
cmd_body = {"body_yaw": 0.5}  # 弧度（约 30°）
cmd_head = {"head_pose": {"pitch": -0.15}}  # 弧度
```

### 实际可移动范围

| 参数 | API 支持范围 | 实际物理限制 | 建议前端范围 |
|------|------------|-------------|-------------|
| `body_yaw` | ±160° | 约 ±80° | ±80° |
| `head_pose.yaw` | ±160° | ±160° | ±160° |
| `head_pose.roll` | ±25° | ±25° | ±25° |
| `head_pose.pitch` | ±35° | ±35° | ±35° |
| `antennas[]` | ±80° | ±80° | ±80° |

### 实现架构

本 Demo 使用 **WebSocket 中间件** 架构：
```
浏览器 ──[Socket.IO]──> Flask 服务器 ──[HTTP POST]──> 机器人 API
         (度数)              (度→弧度转换)             (弧度)
```

**关键代码** (`server.py:81-122`):
```python
import math

# 头部姿态欧拉角（度转弧度）
roll_radians = math.radians(data.get('roll', 0.0))
pitch_radians = math.radians(data.get('pitch', 0.0))
yaw_radians = math.radians(data.get('yaw', 0.0))

# 天线角度（度转弧度）
antennas_radians = [math.radians(a) for a in data.get('antennas', [0, 0])]

# 身体偏航（度转弧度）
body_yaw_radians = math.radians(data.get('body_yaw', 0.0))

payload = {
    'head_pose': {
        'x': data.get('position', {}).get('x', 0.0),
        'y': data.get('position', {}).get('y', 0.0),
        'z': data.get('position', {}).get('z', 0.0),
        'roll': roll_radians,
        'pitch': pitch_radians,
        'yaw': yaw_radians
    },
    'antennas': antennas_radians,
    'body_yaw': body_yaw_radians,
    'duration': 0.3,
    'interpolation': 'minjerk'
}
```

### 后续开发建议

1. **始终将角度转换为弧度** 再发送给 `/move/goto` API
2. **前端显示度数**（用户友好），**后端转换为弧度**（API 要求）
3. **参考实际工作的 Demo**（如 Demo 06）而非仅依赖文档
4. **添加调试日志** 验证发送的数值是否符合预期

## 注意事项

1. **单位转换**: API 使用弧度，前端显示度数，后端必须转换
2. **网络延迟**: WebSocket 延迟极低，但网络质量仍会影响
3. **更新频率**: 60Hz 会产生更多网络流量，根据需要选择
4. **浏览器兼容**: 需要支持 WebSocket 的现代浏览器
5. **机器人负载**: 高频控制可能增加机器人 CPU 负载
6. **连接稳定性**: 如频繁断线，检查网络质量和机器人状态
7. **实际范围**: body_yaw 实际可移动范围约 ±80°，虽然 API 支持 ±160°

## 故障排除

### WebSocket 无法连接

- 检查机器人是否开机
- 检查 `config.yaml` 中的 IP 地址是否正确
- 尝试在浏览器直接访问 `ws://<机器人IP>:8000/move/ws/set_target`
- 检查防火墙是否阻止 WebSocket 连接

### 控制不平滑

- 降低更新频率到 10Hz
- 检查网络延迟和质量
- 关闭其他占用带宽的程序
- 使用有线网络代替无线网络

### 延迟过高

- 检查网络连接质量
- 使用有线网络
- 降低更新频率
- 检查机器人 CPU 使用率

### 自动重连失败

- 刷新页面重新连接
- 检查机器人是否正常运行
- 重启机器人后重试

## 进阶功能

### 自定义更新频率

修改前端 `updateRate` 选项，添加自定义频率：

```javascript
<select id="updateRate">
    <option value="10">10 Hz</option>
    <option value="30">30 Hz</option>
    <option value="60">60 Hz</option>
    <option value="120">120 Hz (自定义)</option>
</select>
```

### 添加状态监控

连接状态流 WebSocket 获取机器人实时状态：

```javascript
const stateWS = new WebSocket('ws://<IP>:8000/state/ws/full?frequency=30');
stateWS.onmessage = (event) => {
    const state = JSON.parse(event.data);
    console.log('当前姿态:', state.head_pose);
};
```

### 记录控制轨迹

```javascript
let trajectory = [];

function sendCurrentState() {
    // ... 发送命令
    trajectory.push({
        timestamp: Date.now(),
        pose: command.target_head_pose
    });
}
```

## 参考资源

- [Reachy Mini API 参考文档](../../docs/API_REFERENCE_CN.md) - WebSocket 接口详解
- [WebSocket API 文档](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [WebSocket 协议规范](https://datatracker.ietf.org/doc/html/rfc6455)
