# Demo 17: Reachy Mini 网页控制与视频流

这是一个完整的 Reachy Mini 网页控制界面，整合了实时控制和视频流显示功能。

## 功能特点

- **WebSocket 低延迟控制**: 基于 Demo 15，提供 <10ms 延迟的实时控制
- **实时视频流**: 基于 Demo 18，将 WebRTC 视频流转换为 MJPEG 格式在浏览器中显示
- **模块化前端设计**: HTML、CSS、JavaScript 分离，便于维护和扩展
- **现代化 UI 设计**: 渐变色、毛玻璃效果、响应式布局
- **完整机器人控制**: 头部位置、姿态、天线、身体偏航

## 架构设计

```
浏览器 <--[WebSocket]--> Flask 服务器 <--[HTTP POST]--> 机器人 API
     <--[MJPEG]-->      |
                       +--[WebRTC]--> 机器人视频流
```

### 控制链路 (来自 Demo 15)

- 前端发送控制命令（度数）到 Flask 服务器
- 服务器将度数转换为弧度
- 通过 REST API 转发到机器人

### 视频链路 (来自 Demo 18)

- 机器人通过 WebRTC 发送视频流
- GStreamer 接收并转换为 MJPEG
- Flask 提供HTTP MJPEG 流服务
- 浏览器通过 `<img>` 标签显示

## 文件结构

```
17_webcam_robot_control/
├── server.py              # Flask 后端服务器
├── README.md              # 本文档
├── templates/
│   └── index.html         # 主页面模板
└── static/
    ├── css/
    │   └── style.css      # 样式表
    └── js/
        ├── main.js        # 主入口
        ├── control.js     # 控制模块
        └── video.js       # 视频模块
```

## 依赖安装

### Python 依赖

```bash
pip install flask flask-socketio eventlet requests opencv-python numpy
```

### GStreamer 依赖

确保已安装 GStreamer 和 WebRTC 插件（与 reachy-mini SDK 一起安装）

## 使用方法

### 启动服务器

```bash
python server.py --signaling-host <机器人IP>
```

参数说明:
- `--signaling-host`: 机器人 IP 地址（必需）
- `--signaling-port`: 信令服务器端口，默认 8443
- `--peer-name`: 对等端名称，默认 "reachymini"
- `--port`: HTTP 服务端口，默认 5000

### 访问界面

启动后在浏览器中打开:
- 本地访问: `http://localhost:5000`
- 局域网访问: `http://<你的IP>:5000`

## 控制说明

### 快捷操作

- **启用电机**: 激活所有电机，准备接收运动命令
- **禁用电机**: 停用所有电机，机器人保持当前姿态
- **全部回零**: 将所有控制参数重置为零位

### 头部位置控制 (米)

| 轴 | 范围 | 说明 |
|---|------|------|
| X | ±0.05 | 前后位置 |
| Y | ±0.05 | 左右位置 |
| Z | -0.03 ~ +0.08 | 上下位置 |

### 头部姿态控制 (度)

| 轴 | 范围 | 说明 |
|---|------|------|
| Roll | ±25° | 左右翻滚 |
| Pitch | ±35° | 上下俯仰 |
| Yaw | ±160° | 左右偏航 |

### 天线控制 (度)

| 天线 | 范围 |
|---|------|
| 左天线 | ±80° |
| 右天线 | ±80° |

### 身体控制 (度)

| 轴 | 范围 |
|---|------|
| Body Yaw | ±160° |

### 更新频率

- **10 Hz**: 平滑模式，适合精细调整
- **30 Hz**: 推荐设置，平衡性能和响应速度
- **60 Hz**: 极速模式，最小延迟

## 技术细节

### 单位转换

前端使用度数（用户友好），后端自动转换为弧度（API 要求）:

```
radians = degrees × π / 180
```

### 防抖处理

滑块输入采用 20ms 防抖，避免频繁发送命令:

```javascript
// 防抖发送命令
debounceTimer = setTimeout(() => {
    sendMoveCommand();
}, 20);
```

### 视频流技术

- 使用 GStreamer `webrtcsrc` 接收 WebRTC 流
- 转换为 BGR 格式 (OpenCV 兼容)
- JPEG 编码质量: 85
- 帧率: ~30 FPS
- 延迟: 100-300ms

## 浏览器兼容性

- Chrome/Edge: 完全支持
- Firefox: 完全支持
- Safari: 完全支持
- 移动浏览器: 支持响应式布局

## 故障排除

### 视频无法连接

1. 确认机器人 IP 地址正确
2. 检查机器人 WebRTC 服务是否运行
3. 查看浏览器控制台错误信息

### 控制无响应

1. 检查 WebSocket 连接状态（顶部状态指示器）
2. 确认机器人 REST API 可访问
3. 尝试点击"启用电机"按钮

### 延迟过高

1. 降低更新频率到 10 Hz
2. 检查网络连接质量
3. 确认在同一局域网内

## 参考文档

- [Demo 15: 实时控制](../15_web_realtime_control/README.md)
- [Demo 18: WebRTC 转换](../18_webrtc_to_http_stream/README.md)
- [Reachy Mini API 文档](../../docs/API_REFERENCE.md)

## 许可证

与 Reachy Mini 项目相同
