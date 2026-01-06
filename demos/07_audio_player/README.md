# Demo 07: 音频播放器

使用 Reachy Mini 的内置扬声器播放音频，支持本地文件和在线 URL。

---

## 运行平台

| 平台 | 支持情况 |
|------|----------|
| PC   | ❌ 不适用 |
| Reachy Mini | ✅ 支持 |

> 此 demo 必须在 Reachy Mini 上运行，使用其内置硬件扬声器。

---

## 功能特性

- **本地文件播放** - 支持播放本地存储的音频文件
- **在线 URL 播放** - 自动下载并播放网络音频
- **多格式支持** - WAV, MP3, FLAC, OGG
- **自动音频处理**:
  - 多声道转单声道
  - 自动重采样到 16kHz
  - 准确的播放时长计算
- **自动清理** - 下载的临时文件播放后自动删除

---

## 前置条件

### 1. 系统要求

- **操作系统**: Linux (Reachy Mini)
- **Python**: 3.7+
- **网络**: 在线播放需要网络连接

### 2. Python 依赖

```bash
# 在 Reachy Mini 上安装依赖
pip install numpy scipy soundfile requests

# 或使用 uv
uv pip install numpy scipy soundfile requests
```

---

## 使用方法

### 方式 1: 命令行参数 (推荐)

```bash
# 播放本地文件
python3 audio_player.py /path/to/audio.wav

# 播放在线 URL
python3 audio_player.py https://example.com/audio.mp3
```

### 方式 2: 修改脚本内列表

编辑 `audio_player.py`，在 `test_sources` 列表中添加音频源:

```python
test_sources = [
    # 本地文件
    "/home/user/music.wav",

    # 在线 URL
    "https://example.com/audio.mp3",
]
```

然后运行:
```bash
python3 audio_player.py
```

---

## 支持的音频格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| WAV | `.wav` | 无损格式，推荐 |
| MP3 | `.mp3` | 有损压缩，通用 |
| FLAC | `.flac` | 无损压缩 |
| OGG | `.ogg` | 开源格式 |

---

## 音频处理流程

```
输入 (本地/URL)
    ↓
解码 (soundfile)
    ↓
转单声道 (多声道 → 单声道)
    ↓
重采样 (任意采样率 → 16kHz)
    ↓
分块推送 (1024 samples/chunk)
    ↓
播放完成 + 清理临时文件
```

---

## 示例输出

### 播放本地文件

```
检测到本地路径: /home/user/test.wav
正在读取/解码音频...
原始信息:
  采样率: 44100 Hz
  声道: 2
转换为单声道...
重采样到 16000 Hz...
预计播放时长: 5.23 秒

开始播放...
等待播放结束...
播放完成!
```

### 播放在线 URL

```
检测到在线链接，正在下载: https://example.com/audio.mp3
已下载到临时文件: /tmp/tmpXXX.mp3
正在读取/解码音频...
原始信息:
  采样率: 48000 Hz
  声道: 1
重采样到 16000 Hz...
预计播放时长: 10.50 秒

开始播放...
等待播放结束...
播放完成!
临时文件已清理
```

---

## API 说明

### ReachyMini 媒体 API

```python
# 开始播放
mini.media.start_playing()

# 推送音频数据 (numpy array)
mini.media.push_audio_sample(audio_chunk)

# 停止播放
mini.media.stop_playing()
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source` | str | 必填 | 音频路径 (本地) 或 URL |
| `resample` | bool | True | 是否重采样到 16kHz |
| `target_sr` | int | 16000 | 目标采样率 (Hz) |

---

## 故障排除

### 问题 1: 找不到本地文件

**错误信息**: `错误: 找不到文件 /path/to/audio.wav`

**解决**:
- 检查文件路径是否正确 (使用绝对路径)
- 确认文件存在且可读

### 问题 2: 在线下载失败

**错误信息**: `下载失败: HTTPConnectionPool...`

**解决**:
- 检查网络连接
- 确认 URL 可访问
- 尝试使用其他音频源

### 问题 3: 导入模块失败

**错误信息**: `ModuleNotFoundError: No module named 'soundfile'`

**解决**:
```bash
pip install soundfile
```

### 问题 4: 音频播放卡顿

**原因**: 采样率不匹配或网络延迟

**解决**:
- 使用本地文件而非在线 URL
- 确保音频采样率接近 16kHz

---

## 音频质量建议

| 用途 | 推荐格式 | 推荐采样率 | 说明 |
|------|----------|------------|------|
| 语音 | WAV/MP3 | 16kHz | 平衡质量和大小 |
| 音乐 | FLAC | 44.1kHz+ | 高质量 |
| 测试 | WAV | 16kHz | 简单直接 |

---

## 相关文档

- [API 参考文档](../../docs/API_REFERENCE_CN.md)
- [媒体 API 说明](../../docs/MEDIA_API_CN.md)

---

## 许可证

MIT License
