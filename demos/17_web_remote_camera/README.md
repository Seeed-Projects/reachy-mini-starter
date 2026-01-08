# Demo 17: 网页版遥控摄像头

通过浏览器控制 Reachy Mini 机器人头部摄像头，实现局域网内的远程监控和头部运动控制。

## 功能特点

- 🌐 **Web 界面控制** - 通过浏览器控制，无需安装客户端
- 🎮 **头部运动控制** - 支持 Yaw（左右）、Pitch（上下）、Roll（倾斜）、Z（前后）控制
- ⚡ **实时响应** - 使用 WebSocket 实现实时双向通信
- 📱 **响应式设计** - 支持桌面和移动设备
- 🎯 **快捷位置** - 预设常用视角位置
- ⌨️ **键盘控制** - 支持方向键控制头部运动
- 🔧 **电机控制** - 支持启用/禁用电机，方便手动调整

## 文件结构

```
17_web_remote_camera/
├── server.py              # Flask + WebSocket 后端服务器
├── templates/
│   └── index.html        # 前端页面
├── static/
│   ├── style.css         # 样式文件
│   └── app.js            # 前端逻辑
└── README.md             # 本文档
```

## 快速开始

### 前置要求

1. Python 3.7+
2. Reachy Mini 机器人（已连接同一网络）
3. 配置好机器人 IP 地址（`demos/robot_config.yaml`）

### 安装依赖

```bash
pip install flask flask-socketio eventlet requests
```

### 运行服务器

```bash
cd demos/17_web_remote_camera
python server.py
```

启动后会显示访问地址：
- 本地访问: `http://localhost:5000`
- 局域网访问: `http://<本机IP>:5000`

### 访问控制页面

在局域网内的任何设备浏览器中打开服务器地址即可开始控制。

## 使用说明

### 头部运动控制

**Yaw（左右转动）**
- 范围: -160° ~ +160°
- 控制机器人头部左右转动

**Pitch（上下俯仰）**
- 范围: -35° ~ +35°
- 控制机器人头部上下运动

**Roll（左右倾斜）**
- 范围: -25° ~ +25°
- 控制机器人头部左右倾斜

**Z（前后位置）**
- 范围: -30mm ~ +80mm
- 控制机器人头部前后位置

### 快捷位置

- **向前看** - 头部回到正前方
- **向左看** - 头部向左转动 45°
- **向右看** - 头部向右转动 45°
- **向上看** - 头部向上仰 25°
- **向下看** - 头部向下俯 25°

### 键盘快捷键

- `←` / `→` - 左右转动头部
- `↑` / `↓` - 上下运动头部
- `R` - 重置头部位置

### 电机控制

- **启用电机** - 启用电机控制，可以进行运动控制
- **禁用电机** - 禁用电机，可以手动移动头部调整位置

## 视频流

由于浏览器的安全限制，视频流需要单独的客户端程序接收。

### 接收视频流

1. 打开新的终端窗口
2. 运行视频流接收程序：

```bash
cd demos/05_webrtc_video_stream
python3 05.py --signaling-host <机器人IP>
```

3. 视频流窗口会自动打开并显示机器人的摄像头画面

### 关于 WebRTC

- 视频流使用 GStreamer WebRTC 协议传输
- 需要安装 GStreamer 和 WebRTC 插件
- 详见项目文档中的 GStreamer 安装指南

## 网络配置

### 局域网访问

确保防火墙允许端口 5000：

```bash
# Linux (ufw)
sudo ufw allow 5000

# Linux (firewalld)
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

### 跨网段访问

如需跨网段访问，可以：

1. 使用端口转发：`ssh -L 5000:localhost:5000 user@server`
2. 配置 VPN 连接到机器人网络
3. 使用 frp 或 ngrok 等内网穿透工具

## API 接口

### WebSocket 事件

**客户端 → 服务器**

| 事件 | 参数 | 说明 |
|-----|------|------|
| `move_head` | `{axis, value, duration}` | 移动头部 |
| `reset_head` | - | 重置头部位置 |
| `enable_motors` | - | 启用电机 |
| `disable_motors` | - | 禁用电机 |
| `check_connection` | - | 检查连接状态 |

**服务器 → 客户端**

| 事件 | 参数 | 说明 |
|-----|------|------|
| `status` | `{connected, robot_ip, video_url}` | 连接状态 |
| `connection_status` | `{connected}` | 机器人连接状态 |
| `move_result` | `{success, axis, value, error}` | 运动结果 |
| `reset_result` | `{success, error}` | 重置结果 |
| `motors_result` | `{action, success, error}` | 电机操作结果 |

## 故障排除

### 无法连接到机器人

1. 检查机器人是否开机
2. 检查 `demos/robot_config.yaml` 中的 IP 地址是否正确
3. 尝试 ping 机器人 IP: `ping <机器人IP>`
4. 检查防火墙设置

### 控制无响应

1. 检查浏览器控制台是否有错误（F12）
2. 确认电机已启用
3. 查看操作日志中的错误信息
4. 重新加载页面

### 视频无法显示

1. 确保已安装 GStreamer 和 WebRTC 插件
2. 检查机器人是否开启视频流服务
3. 查看 GStreamer 客户端的错误输出
4. 详见 GStreamer 安装指南

## 技术栈

- **后端**: Flask + Flask-SocketIO + eventlet
- **前端**: 原生 HTML/CSS/JavaScript + Socket.IO
- **通信**: WebSocket (Socket.IO)
- **机器人 API**: REST API

## 扩展建议

可以添加的功能：

- [ ] 录像功能 - 保存视频流到本地
- [ ] 截图功能 - 保存当前画面
- [ ] 预设轨迹 - 保存和回放头部运动轨迹
- [ ] 多用户支持 - 支持多个用户同时观看
- [ ] 语音控制 - 集成语音识别进行头部控制
- [ ] 自动跟踪 - 结合视觉算法自动跟踪目标
- [ ] 虚拟现实 - 支持 VR 设备控制

## 相关文档

- [Demo 05: WebRTC 视频流](../05_webrtc_video_stream/)
- [Demo 11: YOLO 视觉控制](../11_yolo_robot_control/)
- [API 参考文档](../../docs/API_REFERENCE_CN.md)

## 许可证

MIT License
