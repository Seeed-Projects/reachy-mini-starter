# Demo 18: WebRTC 视频流转 HTTP 流

将机器人的 WebRTC 视频流转换为普通的 HTTP MJPEG 流，使其可以在浏览器中直接播放，无需 WebRTC 客户端。

## 功能特点

- **WebRTC 接收** - 使用 GStreamer 接收机器人的 WebRTC 视频流（参考 Demo 11 的实现方式）
- **格式转换** - 将 WebRTC 流转换为 MJPEG（Motion JPEG）格式
- **浏览器播放** - 通过 HTTP 提供视频流，任何浏览器都可以直接播放
- **简单易用** - 无需安装客户端，打开浏览器即可观看
- **实时传输** - 低延迟的视频流传输
- **跨平台** - 支持桌面和移动设备

## 架构说明

```
机器人 --[WebRTC]--> 本服务 --[MJPEG]--> 浏览器
                    18.py
                    (GStreamer + Flask)
```

**技术细节：**
1. **WebRTC 接收** - 使用 GStreamer 的 `webrtcsrc` 元素接收 WebRTC 流
2. **格式转换** - 将视频帧转换为 BGR 格式，然后编码为 JPEG
3. **HTTP 流式传输** - 使用 Flask 的 multipart 响应流式传输 MJPEG
4. **浏览器显示** - 通过 `<img>` 标签的 `src` 属性直接显示视频流

## 快速开始

### 前置要求

1. Python 3.7+
2. Reachy Mini 机器人（已连接同一网络）
3. GStreamer 1.20+ 及 WebRTC 插件
4. 机器人已开启 WebRTC 视频流服务

### 安装依赖

```bash
pip install flask opencv-python numpy
```

### 运行

```bash
cd demos/18_webrtc_to_http_stream
python3 18.py --signaling-host <机器人IP>
```

**示例：**
```bash
python3 18.py --signaling-host 10.42.0.75
```

**命令行参数：**
```bash
python3 18.py \
    --signaling-host 10.42.0.75 \  # 信令服务器地址（机器人 IP）
    --signaling-port 8443 \         # 信令服务器端口
    --peer-name reachymini \        # 对等端名称
    --port 5000                      # HTTP 服务器端口
```

**快捷启动（默认参数）：**
```bash
# 使用默认端口 8443 和对等端名 reachymini
python3 18.py --signaling-host 10.42.0.75

# 自定义 HTTP 端口（避免端口冲突）
python3 18.py --signaling-host 10.42.0.75 --port 8000
```

### 访问视频流

启动服务后，在浏览器中打开：
- 本地访问: `http://localhost:5000`
- 局域网访问: `http://<本机IP>:5000`

## 界面预览

启动服务后，浏览器会显示一个现代化的视频流页面：

**页面布局：**
- 顶部状态栏：显示连接状态和信令服务器地址
- 中央视频区域：显示机器人的实时视频流
- 使用说明：操作提示和功能说明

**状态指示：**
- 🟢 绿色圆点 - 已连接到视频流
- 🔴 红色圆点 - 连接失败或断开
- ⚪ 灰色圆点（动画） - 正在连接

## 使用说明

### 观看视频

1. 运行服务后，浏览器会自动显示视频流
2. 视频流以 MJPEG 格式传输，浏览器会自动解码并显示
3. 支持所有现代浏览器（Chrome、Firefox、Safari、Edge）

### 状态指示

页面顶部显示连接状态：
- **绿色圆点** - 已连接到视频流
- **红色圆点** - 连接失败

### 移动设备访问

在移动设备（手机/平板）上也可以访问：

1. 确保移动设备和运行服务的电脑在同一网络
2. 在移动设备浏览器中输入：`http://<电脑IP>:5000`
3. 视频流会自动适配屏幕大小

### 直接访问视频流

如果你只想获取原始视频流（不使用网页界面），可以直接访问：

```
http://<服务器IP>:5000/video_feed
```

这可以用于：
- 在其他应用中嵌入视频流
- 使用 `<img>` 标签在自定义页面中显示
- 与视频处理软件集成

**示例：在自定义 HTML 中嵌入**
```html
<!DOCTYPE html>
<html>
<head>
    <title>自定义视频播放器</title>
</head>
<body>
    <h1>机器人视频流</h1>
    <img src="http://localhost:5000/video_feed" alt="视频流" style="width: 100%;">
</body>
</html>
```

### API 接口

服务提供以下 HTTP 接口：

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/` | GET | 主页面（带播放器） |
| `/video_feed` | GET | MJPEG 视频流 |
| `/status` | GET | 服务状态信息 |

**状态接口示例：**
```bash
curl http://localhost:5000/status
# 返回: {"status": "running", "signalling_host": "10.42.0.75", "signalling_port": 8443}
```

## 故障排除

**无法连接到视频流**
1. 检查机器人是否开机
2. 检查机器人 IP 是否正确
3. 确保机器人已开启 WebRTC 服务
4. 尝试 ping 机器人 IP: `ping <机器人IP>`

**视频卡顿或延迟**
1. 检查网络连接质量
2. 尝试降低 JPEG 质量修改代码中的 `IMWRITE_JPEG_QUALITY` 参数
3. 检查 CPU 使用率

**浏览器无法播放**
1. 确保使用现代浏览器
2. 检查浏览器控制台是否有错误（F12）
3. 尝试刷新页面

**端口被占用**
```bash
# 查看端口占用
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# 使用其他端口启动
python3 18.py --signaling-host 10.42.0.75 --port 5001
```

**GStreamer 错误**
1. 确保已安装 GStreamer 1.20+
2. 安装 WebRTC 插件：`libgstreamer-plugins-bad1.0`
3. 参考 [GStreamer 安装指南](../../docs/GSTREAMER_CN.md)

## 使用场景

### 场景 1：远程监控

在办公室监控家中或实验室的机器人：

```bash
# 在机器人网络环境运行
python3 18.py --signaling-host 10.42.0.75 --port 5000
```

然后通过任何设备的浏览器访问监控页面。

### 场景 2：多人同时观看

多个用户可以同时访问视频流：

```bash
# 用户 1
http://10.42.0.100:5000

# 用户 2
http://10.42.0.101:5000

# 用户 3（移动设备）
http://10.42.0.100:5000
```

### 场景 3：集成到现有系统

将视频流嵌入到现有的 Web 应用中：

```html
<iframe src="http://video-server:5000/video_feed"
        width="640" height="480"
        frameborder="0">
</iframe>
```

### 场景 4：视频录制

使用第三方工具录制视频流：

```bash
# 使用 ffmpeg 录制
ffmpeg -i http://localhost:5000/video_feed -t 60 output.mp4
```

## 性能参考

**典型性能指标：**
- 延迟：100-300ms（取决于网络）
- 分辨率：640x480（默认）
- 帧率：15-30 FPS
- 带宽：1-3 Mbps

**系统要求：**
- CPU: 双核 2.0GHz+
- 内存: 2GB+
- 网络: 局域网（推荐）或宽带

## 与其他 Demo 的区别

| Demo | 视频传输方式 | 需要客户端 | 浏览器播放 | 用途 |
|------|------------|----------|-----------|------|
| 05 | WebRTC | 是 | 否 | 本地观看 |
| 11 | WebRTC + OpenCV | 是 | 否 | YOLO 视觉检测 |
| 15 | 无视频流 | 否 | 否 | 网页控制 |
| 17 | 需要单独客户端 | 是 | 否 | 网页控制 |
| **18** | **WebRTC → MJPEG** | **否** | **是** | **浏览器观看** |

## 技术栈

- **GStreamer** - WebRTC 流接收和处理
- **OpenCV** - 视频帧处理和 JPEG 编码
- **Flask** - HTTP 服务器
- **MJPEG** - 视频流格式（multipart/x-mixed-replace）

## MJPEG 格式说明

MJPEG（Motion JPEG）是一种视频流格式，每个视频帧都是一个独立的 JPEG 图片。通过 HTTP 的 multipart 响应流式传输：

```
HTTP/1.1 200 OK
Content-Type: multipart/x-mixed-replace; boundary=frame

--frame
Content-Type: image/jpeg

<JPEG 数据>
--frame
Content-Type: image/jpeg

<JPEG 数据>
...
```

浏览器通过 `<img>` 标签接收并自动刷新显示。

## 代码结构

```
18_webrtc_to_http_stream/
├── 18.py                  # 主程序
│   ├── WebRTCVideoStreamer  # WebRTC 视频流接收器
│   ├── MJPEGServer          # MJPEG HTTP 服务器
│   └── main()               # 主函数
├── templates/
│   └── index.html          # 前端页面
└── README.md              # 本文档
```

## 扩展建议

可以添加的功能：
- [ ] 录像功能 - 保存视频流到本地文件
- [ ] 截图功能 - 保存当前画面为图片
- [ ] 视频质量控制 - 动态调整 JPEG 质量
- [ ] 多分辨率支持 - 支持多种视频分辨率
- [ ] 音频流 - 添加音频流支持
- [ ] 用户认证 - 添加访问控制
- [ ] 多用户支持 - 支持多个用户同时观看
- [ ] 视频录制计划 - 定时录制视频

## 性能优化

**降低延迟：**
1. 设置 `appsink` 的 `sync=False` - 不同步，降低延迟
2. 设置 `max-buffers=1` - 只保留最新帧
3. 设置 `drop=True` - 丢弃旧帧
4. 降低 JPEG 质量 - 减少数据量

**提高质量：**
1. 提高 JPEG 质量（`IMWRITE_JPEG_QUALITY`）
2. 使用更大的缓冲区
3. 优化网络连接

## 相关文档

- [Demo 05: WebRTC 视频流](../05_webrtc_video_stream/)
- [Demo 11: YOLO 视觉控制](../11_yolo_robot_control/)
- [Demo 15: 网页实时控制](../15_web_realtime_control/)
- [Demo 17: 网页遥控摄像头](../17_web_remote_camera/)
- [GStreamer 文档](https://gstreamer.freedesktop.org/documentation/)
- [Flask 文档](https://flask.palletsprojects.com/)

## 许可证

MIT License
