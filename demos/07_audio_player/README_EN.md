# Demo 07: Audio Player

Play audio through Reachy Mini's built-in speaker, supporting both local files and online URLs.

---

## Platform Support

| Platform | Support |
|----------|---------|
| PC   | ❌ Not Applicable |
| Reachy Mini | ✅ Supported |

> This demo must run on Reachy Mini hardware to use the built-in speaker.

---

## Features

- **Local File Playback** - Play audio files stored locally
- **Online URL Playback** - Automatically download and play web audio
- **Multiple Formats** - WAV, MP3, FLAC, OGG
- **Automatic Audio Processing**:
  - Multi-channel to mono conversion
  - Auto resampling to 16kHz
  - Accurate playback duration calculation
- **Auto Cleanup** - Temporary downloaded files are automatically deleted after playback

---

## Prerequisites

### 1. System Requirements

- **OS**: Linux (Reachy Mini)
- **Python**: 3.7+
- **Network**: Required for online URL playback

### 2. Python Dependencies

```bash
# Install dependencies on Reachy Mini
pip install numpy scipy soundfile requests

# Or using uv
uv pip install numpy scipy soundfile requests
```

---

## Usage

### Method 1: Command Line Argument (Recommended)

```bash
# Play local file
python3 audio_player.py /path/to/audio.wav

# Play online URL
python3 audio_player.py https://example.com/audio.mp3
```

### Method 2: Modify Script List

Edit `audio_player.py` and add audio sources to `test_sources`:

```python
test_sources = [
    # Local file
    "/home/user/music.wav",

    # Online URL
    "https://example.com/audio.mp3",
]
```

Then run:
```bash
python3 audio_player.py
```

---

## Supported Audio Formats

| Format | Extension | Description |
|------|--------|------|
| WAV | `.wav` | Lossless, recommended |
| MP3 | `.mp3` | Lossy compression, universal |
| FLAC | `.flac` | Lossless compression |
| OGG | `.ogg` | Open source format |

---

## Audio Processing Pipeline

```
Input (Local/URL)
    ↓
Decode (soundfile)
    ↓
Convert to Mono (multi-channel → mono)
    ↓
Resample (any sample rate → 16kHz)
    ↓
Push in chunks (1024 samples/chunk)
    ↓
Playback complete + cleanup
```

---

## Example Output

### Playing Local File

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

### Playing Online URL

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

## API Reference

### ReachyMini Media API

```python
# Start playback
mini.media.start_playing()

# Push audio data (numpy array)
mini.media.push_audio_sample(audio_chunk)

# Stop playback
mini.media.stop_playing()
```

### Parameters

| Parameter | Type | Default | Description |
|------|------|---------|------|
| `source` | str | Required | Audio path (local) or URL |
| `resample` | bool | True | Whether to resample to 16kHz |
| `target_sr` | int | 16000 | Target sample rate (Hz) |

---

## Troubleshooting

### Issue 1: Local File Not Found

**Error**: `错误: 找不到文件 /path/to/audio.wav`

**Solution**:
- Check if the file path is correct (use absolute path)
- Confirm the file exists and is readable

### Issue 2: Online Download Failed

**Error**: `下载失败: HTTPConnectionPool...`

**Solution**:
- Check network connection
- Verify URL is accessible
- Try a different audio source

### Issue 3: Module Import Failed

**Error**: `ModuleNotFoundError: No module named 'soundfile'`

**Solution**:
```bash
pip install soundfile
```

### Issue 4: Audio Playback Stuttering

**Cause**: Sample rate mismatch or network latency

**Solution**:
- Use local files instead of online URLs
- Ensure audio sample rate is close to 16kHz

---

## Audio Quality Recommendations

| Use Case | Recommended Format | Sample Rate | Notes |
|------|----------|------------|------|
| Speech | WAV/MP3 | 16kHz | Balance quality and size |
| Music | FLAC | 44.1kHz+ | High quality |
| Testing | WAV | 16kHz | Simple and direct |

---

## Related Documentation

- [API Reference](../../docs/API_REFERENCE_EN.md)
- [Media API Documentation](../../docs/MEDIA_API_EN.md)

---

## License

MIT License
