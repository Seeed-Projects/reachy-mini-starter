# Demo 08: 音频流 API 服务

通过 REST API 在局域网内远程控制 Reachy Mini 播放音频，或将 PC 音频实时推流到 Reachy Mini 播放（远程音响功能）。

---

## 运行平台

| 平台 | 支持情况 |
|------|----------|
| PC   | ✅ 客户端 |
| Reachy Mini | ✅ 服务端 |

> 此 demo 分为两部分:
> - **服务端** - 运行在 Reachy Mini 上，提供 API 服务
> - **客户端** - 运行在局域网内的任意设备上，调用 API

---

## 功能特性

### 服务端 (Reachy Mini)
- **本地文件播放** - 通过 API 播放机器人存储的音频文件
- **在线 URL 播放** - 自动下载并播放在线音频
- **PCM 音频流接收** - 接收 UDP 原始 PCM 音频流并实时播放
- **OPUS 音频流接收** - 接收 RTP/OPUS 编码的音频流
- **状态查询** - 获取当前服务状态

### 客户端 (任意设备)
- **Python SDK** - 提供易用的 Python 客户端类
- **命令行工具** - 快速测试所有 API 功能
- **Curl 支持** - 可使用 curl 命令直接调用
- **实时推流** - 将 PC 音频实时推流到 Reachy Mini 播放 (远程音响)

---

## 前置条件

### 1. 系统要求

- **服务端**: Reachy Mini (Linux)
- **客户端**: 任意支持 Python 的设备
- **网络**: 设备在同一局域网

### 2. Python 依赖

```bash
# 服务端依赖 (Reachy Mini)
pip install fastapi uvicorn pydantic numpy scipy soundfile requests gobject

# 客户端基础依赖
pip install requests

# 实时推流功能 - Windows/macOS
pip install pyaudio numpy

# 实时推流功能 - Linux
pip install numpy
# Linux 自带 pulseaudio，无需额外安装
```

---

## 使用方法

### 第一步: 启动服务端 (Reachy Mini)

```bash
cd demos/08_audio_stream_api
python3 audio_stream_server.py
```

服务将监听 `0.0.0.0:8001`，可从局域网内任意设备访问。

---

### 第二步: 选择使用方式

#### 方式 1: 播放本地文件 (Reachy Mini 上的文件)

```bash
curl -X POST http://10.42.0.75:8001/stream/play_file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/home/pollen/prompt_audio_1.wav"}'
```

#### 方式 2: 播放在线音频 URL

```bash
curl -X POST http://10.42.0.75:8001/stream/play_url \
  -H "Content-Type: application/json" \
  -d '{"url": "http://hk2.w0x7ce.eu/prompt_audio_1.wav"}'
```

#### 方式 3: 实时音频推流 (远程音响) ⭐

**这是最强大的功能** - 将你的 PC 变成远程音响发射器！

**工作原理:**
1. 在 PC 上运行推流脚本
2. 脚本会捕获 PC 的系统音频输出
3. 实时传输到 Reachy Mini 播放
4. 你在 PC 上播放的任何声音（音乐、视频、游戏音效等）都会在 Reachy Mini 上同步播放

**使用步骤:**

```bash
# === Windows 用户 ===
# 1. 首先启用 "立体声混音" (Stereo Mix)
#    - 右键任务栏音量图标 → "打开声音设置"
#    - 点击 "更多声音设置"
#    - 切换到 "录制" 选项卡
#    - 右键空白处 → "显示已禁用的设备"
#    - 启用 "立体声混音" 并设为默认录制设备

# 2. 运行推流脚本
python3 stream_pc_audio.py --robot-ip 10.42.0.75

# === macOS 用户 ===
# 1. 安装虚拟音频设备
brew install blackhole
# 或使用 Soundflower

# 2. 运行推流脚本
python3 stream_pc_audio.py --robot-ip 10.42.0.75

# === Linux 用户 ===
# 1. 列出可用的音频源 (首次使用)
python3 stream_pc_audio_pulse.py --robot-ip 10.42.0.75 --list-sources

# 2. 使用 PulseAudio 的 monitor device 推流 (推荐)
python3 stream_pc_audio_pulse.py --robot-ip 10.42.0.75 --parec
```

**使用技巧:**
- 🎵 播放音乐：在 PC 上打开音乐播放器，声音会在 Reachy Mini 上播放
- 🎬 观看视频：播放视频，声音会在 Reachy Mini 上同步
- 🎮 游戏：游戏音效也会传输到 Reachy Mini
- 🔇 静音控制：PC 端静音不影响传输（因为捕获的是系统输出）

---

## API 端点

### POST /stream/start_pcm
启动 PCM 音频流接收 (用于实时推流)

**请求体:**
```json
{
  "port": 5001,           // UDP 端口 (可选)
  "sample_rate": 48000,   // 采样率 (可选)
  "channels": 1           // 声道数 (可选)
}
```

**响应:**
```json
{
  "status": "started",
  "format": "PCM S16LE",
  "port": 5001,
  "sample_rate": 48000,
  "channels": 1,
  "audio_device": "reachymini_audio_sink"
}
```

### POST /stream/start
启动 OPUS 音频流接收 (用于 RTP/OPUS 编码流)

**请求体:**
```json
{
  "port": 5001,
  "sample_rate": 48000,
  "channels": 1
}
```

**响应:**
```json
{
  "status": "started",
  "format": "OPUS",
  "port": 5001,
  "sample_rate": 48000,
  "channels": 1
}
```

### POST /stream/stop
停止音频流接收

**响应:**
```json
{
  "status": "stopped",
  "formats": ["PCM", "OPUS"]
}
```

### GET /stream/status
获取流接收状态

**响应:**
```json
{
  "opus_running": false,
  "pcm_running": true,
  "pcm_port": 5001
}
```

### POST /stream/play_file
播放本地音频文件

**请求体:**
```json
{
  "file_path": "/path/to/audio.wav",
  "sample_rate": 16000
}
```

### POST /stream/play_url
播放在线音频 URL

**请求体:**
```json
{
  "url": "https://example.com/audio.wav",
  "sample_rate": 16000
}
```

---

## 实时推流详细说明

### 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                        PC 端                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  音频源 → 回环设备 (Stereo Mix/Monitor) → 推流脚本 │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ UDP PCM 音频流
                            │ (端口 5001)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Reachy Mini 端                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PCM 接收器 → GStreamer → ALSA 扬声器输出          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 推流参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 采样率 | 48000 Hz | 高音质 |
| 声道 | 单声道 (1) | 兼容性最好 |
| 编码 | PCM 16-bit (S16LE) | 无损压缩 |
| 协议 | UDP | 低延迟 |
| 端口 | 5001 | 可配置 |
| 延迟 | ~20-50ms | 取决于网络 |

### 使用技巧

1. **最佳体验**: 使用回环设备可捕获所有系统音频，无需单独配置每个应用
2. **低延迟**: 脚本使用小缓冲区，配合有线网络延迟更低
3. **网络要求**: 建议使用有线网络，WiFi 可能有额外延迟
4. **音频质量**: 48kHz 采样率提供高质量音频传输

### 平台特定配置

#### Windows
1. 右键任务栏音量图标 → "打开声音设置"
2. 点击 "更多声音设置"
3. 切换到 "录制" 选项卡
4. 右键空白处 → "显示已禁用的设备"
5. 启用 "立体声混音" 或 "Wave Out Mix"

#### macOS
```bash
# 安装 BlackHole
brew install blackhole

# 或使用 Soundflower
brew install soundflower
```

#### Linux
```bash
# 查看 monitor 设备
pactl list sources | grep monitor

# 通常设备名为类似：
# alsa_output.pci-0000_00_1f.3.analog-stereo.monitor
```

---

## 应用场景

| 场景 | 描述 | API / 工具 |
|------|------|-----|
| **远程音响** ⭐ | 将 PC 音频实时推流到机器人播放 | `stream_pc_audio_pulse.py --parec` |
| 远程语音播放 | 从服务器推送语音到机器人 | `/stream/play_url` |
| 本地音频播放 | 播放机器人存储的音频 | `/stream/play_file` |
| 实时流媒体 | 低延迟实时音频传输 | `/stream/start_pcm` + UDP |
| 状态监控 | 检查服务是否正常运行 | `/stream/status` |

---

## 故障排除

### 问题 1: 客户端连接失败

**错误**: `❌ 连接失败: 无法连接到 http://10.42.0.75:8001`

**解决**:
1. 检查 Reachy Mini 是否开机
2. 确认服务端已启动 (`ps aux | grep audio_stream_server`)
3. 检查 IP 地址是否正确
4. 确认防火墙未阻止端口 8001

### 问题 2: 找不到音频输入设备

**症状**: "未找到回环设备，使用默认输入设备"

**解决**:
- **Windows**: 需要手动启用 "立体声混音" (见上方平台配置)
- **macOS**: 需要安装 BlackHole 或 Soundflower
- **Linux**: 使用 `stream_pc_audio_pulse.py` 自动检测 monitor 设备

### 问题 3: 推流无声音

**可能原因**:
- 回环设备未正确配置
- 服务端 PCM 接收器未启动
- 防火墙阻止 UDP 5001 端口
- 音频格式不匹配

**解决**:
1. 确认使用了 `/stream/start_pcm` 端点 (不是 `/stream/start`)
2. 检查服务端日志是否显示 "PCM audio stream receiver started successfully"
3. 使用 `curl http://<ROBOT_IP>:8001/stream/status` 检查状态
4. 测试 UDP 连通性: `nc -u 10.42.0.75 5001`

### 问题 4: 音频卡顿或有延迟

**解决**:
1. 使用有线网络替代 WiFi
2. 关闭其他占用带宽的应用
3. 检查网络信号强度
4. 确认 PC 和 Reachy Mini 之间跳数少

---

## 文件说明

| 文件 | 说明 | 运行平台 |
|------|------|----------|
| `audio_stream_server.py` | 服务端 API 服务 | Reachy Mini |
| `test_client.py` | Python 测试客户端 | PC |
| `stream_pc_audio.py` | PyAudio 推流脚本 (Windows/macOS) | PC |
| `stream_pc_audio_pulse.py` | PulseAudio 推流脚本 (Linux) | PC (Linux) |

---

## 相关文档

- [API 参考文档](../../docs/API_REFERENCE_CN.md)
- [网络配置指南](../../docs/NETWORK_GUIDE_CN.md)
- [Demo 07: 音频播放器](../07_audio_player/)

---

## 许可证

MIT License
