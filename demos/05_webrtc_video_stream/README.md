# 📹 Demo 05: WebRTC 视频流接收

使用 GStreamer WebRTC 接收 Reachy Mini 的实时视频和音频流。

---

## 运行平台

| 平台 | 支持情况 |
|------|----------|
| PC   | ✅ 支持 |
| Reachy Mini | ❌ 不适用 |

> 此 demo 在 PC 上运行，接收来自 Reachy Mini 的视频和音频流。

---

## 功能特性

- 实时视频流接收 (来自 Reachy Mini 摄像头)
- 音频流接收 (来自 Reachy Mini 麦克风)
- 自动延迟优化 (50ms 低延迟配置)
- FPS 显示和延迟监控

---

## 前置条件

### 1. 系统要求

- **操作系统**: Linux (Ubuntu 20.04/22.04), macOS, Windows (部分支持)
- **Python**: 3.7+
- **网络**: 与 Reachy Mini 在同一局域网

### 2. GStreamer 安装

此演示需要安装 GStreamer 和 WebRTC 插件。

#### Linux (Ubuntu/Debian)

**基础 GStreamer 安装:**

```bash
sudo apt-get update
sudo apt-get install -y \
    libgstreamer-plugins-bad1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer1.0-dev \
    libglib2.0-dev \
    python3-gi \
    python3-gi-cairo \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-alsa
```

#### Ubuntu 22.04 特殊处理 ⚠️

Ubuntu 22.04 需要使用特定版本的 gst-plugins-rs:

```bash
# 克隆 GStreamer Rust 插件仓库
git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git
cd gst-plugins-rs

# 切换到 0.11.3 版本 (兼容 GStreamer 1.20)
git checkout 0.11.3

# 修复 time 库 Bug
cargo update -p time

# 安装构建工具
cargo install cargo-c

# 创建安装目录
sudo mkdir -p /opt/gst-plugins-rs
sudo chown $USER /opt/gst-plugins-rs

# 编译并安装 WebRTC 插件
cargo cinstall -p gst-plugin-webrtc --prefix=/opt/gst-plugins-rs --release

# 添加到环境变量
echo 'export GST_PLUGIN_PATH=/opt/gst-plugins-rs/lib/x86_64-linux-gnu:$GST_PLUGIN_PATH' >> ~/.bashrc
source ~/.bashrc
```

#### 其他 Linux 版本

```bash
# 克隆仓库
git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git
cd gst-plugins-rs
git checkout 0.14.1

# 安装构建工具
cargo install cargo-c

# 编译安装
sudo mkdir -p /opt/gst-plugins-rs
sudo chown $USER /opt/gst-plugins-rs
cargo cinstall -p gst-plugin-webrtc --prefix=/opt/gst-plugins-rs --release

# 添加到环境变量
echo 'export GST_PLUGIN_PATH=/opt/gst-plugins-rs/lib/x86_64-linux-gnu:$GST_PLUGIN_PATH' >> ~/.bashrc
source ~/.bashrc
```

#### macOS

```bash
brew install gstreamer libnice-gstreamer
```

#### Windows

> ⚠️ Windows 部分支持，请参考 [GSTREAMER.md](../../docs/GSTREAMER.md)

### 3. Python 依赖

```bash
pip install 'reachy-mini[gstreamer]'
# 或使用 uv
uv pip install 'reachy-mini[gstreamer]'
```

---

## 使用方法

### 基本用法

```bash
# 连接到本地 Reachy Mini (默认 127.0.0.1:8443)
python3 05.py

# 连接到指定 IP 的 Reachy Mini
python3 05.py --signaling-host 10.42.0.75

# 完整配置
python3 05.py -s 10.42.0.75 -p 8443
```

### 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--signaling-host` | `-s` | `127.0.0.1` | Reachy Mini 的 IP 地址 |
| `--signaling-port` | `-p` | `8443` | 信令服务器端口 |
| `--peer-name` | `-n` | `reachymini` | 对等体名称 |

---

## 工作原理

```
┌─────────────────┐         WebRTC          ┌──────────────────┐
│  Reachy Mini    │ ◄─────────────────────► │   Your PC        │
│  (Producer)     │     Signaling (ws://)   │   (Consumer)     │
│                 │                          │                  │
│  ┌───────────┐  │                          │  ┌────────────┐  │
│  │  Camera   │  │    Video/Audio Stream    │  │  Display    │  │
│  │  Mic      │  │ ──────────────────────► │  │  Speaker    │  │
│  └───────────┘  │                          │  └────────────┘  │
└─────────────────┘                          └──────────────────┘
```

1. **连接阶段**: 通过 WebSocket 信令服务器与 Reachy Mini 建立 WebRTC 连接
2. **协商阶段**: 交换 SDP (Session Description Protocol) 和 ICE 候选
3. **流传输**: 接收 H.264 视频流和 Opus 音频流
4. **解码显示**: GStreamer 自动解码并显示视频/播放音频

---

## 故障排除

### 问题 1: `webrtcsrc component could not be created`

**原因**: WebRTC 插件未正确安装

**解决**:
```bash
# 检查插件是否安装
gst-inspect-1.0 webrtcsrc

# 如果报错，重新安装 WebRTC 插件 (参考上方安装指南)
```

### 问题 2: `No such file or directory: 'gst_signalling'`

**原因**: 未安装 reachy-mini 的 gstreamer 额外依赖

**解决**:
```bash
pip install 'reachy-mini[gstreamer]'
```

### 问题 3: 连接超时

**原因**: 无法连接到 Reachy Mini

**解决**:
- 检查 Reachy Mini 是否开机
- 检查网络连接
- 确认 IP 地址正确
- 检查防火墙设置

### 问题 4: 有视频但无声音

**原因**: 音频输出设备配置问题

**解决**:
```bash
# 测试音频设备
gst-launch-1.0 audiotestsrc ! autoaudiosink

# 检查 ALSA 设备
aplay -l
```

### 问题 5: 延迟过高

**原因**: 网络抖动缓冲设置过大

**解决**: 代码已将延迟设置为 50ms，如需进一步调整:
```python
# 在 05.py 中修改
webrtcbin.set_property("latency", 30)  # 降低到 30ms
```

---

## 验证 GStreamer 安装

```bash
# 检查版本
gst-launch-1.0 --version

# 测试视频输出
gst-launch-1.0 videotestsrc ! autovideosink

# 测试音频输出
gst-launch-1.0 audiotestsrc ! autoaudiosink

# 验证 WebRTC 插件
gst-inspect-1.0 webrtcsrc
```

---

## 相关文档

- [GStreamer 安装指南 (中文)](../../docs/GSTREAMER_CN.md)
- [GStreamer Installation Guide (English)](../../docs/GSTREAMER.md)
- [网络配置指南](../../docs/NETWORK_GUIDE_CN.md)
- [API 参考文档](../../docs/API_REFERENCE_CN.md)

---

## 技术细节

### 视频编解码

- **编码**: H.264 (硬件加速)
- **分辨率**: 640x480 (可配置)
- **帧率**: 30 FPS

### 音频编解码

- **编码**: Opus
- **采样率**: 48 kHz
- **通道**: 单声道

### 网络协议

- **信令**: WebSocket (ws://IP:8443)
- **传输**: WebRTC RTP/RTCP
- **NAT 穿透**: ICE, STUN

---

## 许可证

MIT License
