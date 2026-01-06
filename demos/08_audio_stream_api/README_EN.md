# Demo 08: Audio Stream API Service

Control Reachy Mini audio playback remotely via REST API from anywhere in the LAN.

---

## Platform Support

| Platform | Support |
|----------|---------|
| PC   | ✅ Client |
| Reachy Mini | ✅ Server |

> This demo has two parts:
> - **Server** - Runs on Reachy Mini, provides API service
> - **Client** - Runs on any device in the LAN, calls the API

---

## Features

### Server (Reachy Mini)
- **Local File Playback** - Play audio files stored on the robot via API
- **Online URL Playback** - Automatically download and play online audio
- **UDP Stream Reception** - Receive UDP audio streams and play in real-time (OPUS encoded)
- **Status Query** - Get current service status

### Client (Any Device)
- **Python SDK** - Easy-to-use Python client class
- **CLI Tool** - Quickly test all API functions
- **Curl Support** - Use curl commands directly
- **Live Streaming** - Stream PC audio to Reachy Mini in real-time (remote speaker)

---

## Prerequisites

### 1. System Requirements

- **Server**: Reachy Mini (Linux)
- **Client**: Any device with Python support
- **Network**: Devices on the same LAN

### 2. Python Dependencies

```bash
# Server dependencies (Reachy Mini)
pip install fastapi uvicorn pydantic numpy scipy soundfile requests gobject

# Client dependencies (any device)
pip install requests

# For live streaming feature
pip install pyaudio numpy
```

---

## Usage

### Step 1: Start Server (Reachy Mini)

```bash
cd demos/08_audio_stream_api
python3 audio_stream_server.py
```

The service will listen on `0.0.0.0:8001`, accessible from any device in the LAN.

### Step 2: Call API from Client

#### Method 1: Using Python Client

```bash
# Run on PC
python3 test_client.py --robot-ip 10.42.0.75

# Test only file playback
python3 test_client.py --robot-ip 10.42.0.75 --test-only file

# Show curl command examples
python3 test_client.py --curl-examples
```

#### Method 2: Using Curl Commands

```bash
# 1. Play local file
curl -X POST http://10.42.0.75:8001/stream/play_file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/home/pollen/prompt_audio_1.wav"}'

# 2. Play local file (with sample rate)
curl -X POST http://10.42.0.75:8001/stream/play_file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/home/pollen/prompt_audio_1.wav", "sample_rate": 16000}'

# 3. Check service status
curl http://10.42.0.75:8001/stream/status

# 4. Start UDP stream reception
curl -X POST http://10.42.0.75:8001/stream/start \
  -H "Content-Type: application/json" \
  -d '{"port": 5001, "sample_rate": 48000, "channels": 1}'

# 5. Stop UDP stream reception
curl -X POST http://10.42.0.75:8001/stream/stop

# 6. Play online audio URL
curl -X POST http://10.42.0.75:8001/stream/play_url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/audio.wav"}'
```

#### Method 3: Live Audio Streaming (Remote Speaker)

Stream PC audio output to Reachy Mini in real-time:

```bash
# List available audio devices (first time use)
python3 stream_pc_audio.py --robot-ip 10.42.0.75 --list-devices

# Stream with default device
python3 stream_pc_audio.py --robot-ip 10.42.0.75

# Auto-detect and use loopback device (e.g., Stereo Mix)
python3 stream_pc_audio.py --robot-ip 10.42.0.75 --auto-loopback

# Specify audio device index
python3 stream_pc_audio.py --robot-ip 10.42.0.75 --device 3
```

**Windows Users**: Enable "Stereo Mix"
1. Right-click volume icon → "Open Sound Settings"
2. Click "More sound settings" or "Sound Control Panel"
3. Switch to "Recording" tab
4. Right-click empty area → "Show Disabled Devices"
5. Enable "Stereo Mix" and set as default recording device

**macOS Users**: Install virtual audio device
```bash
brew install blackhole
# or use Soundflower
```

**Linux Users**: Use PulseAudio monitor device
```bash
pactl list sources | grep monitor
```

---

## API Endpoints

### POST /stream/start
Start UDP audio stream reception

**Request Body:**
```json
{
  "port": 5001,           // UDP port (optional)
  "sample_rate": 48000,   // Sample rate (optional)
  "channels": 1           // Number of channels (optional)
}
```

**Response:**
```json
{
  "status": "started",
  "port": 5001,
  "sample_rate": 48000,
  "channels": 1,
  "audio_device": "reachymini_audio_sink"
}
```

### POST /stream/stop
Stop UDP audio stream reception

**Response:**
```json
{
  "status": "stopped"
}
```

### GET /stream/status
Get current status

**Response:**
```json
{
  "is_running": true,
  "port": 5001,
  "audio_device": "reachymini_audio_sink"
}
```

### POST /stream/play_file
Play local audio file

**Request Body:**
```json
{
  "file_path": "/path/to/audio.wav",   // File path
  "sample_rate": 16000                 // Target sample rate (optional)
}
```

**Response:**
```json
{
  "status": "playing",
  "file_path": "/path/to/audio.wav",
  "target_sample_rate": 16000
}
```

### POST /stream/play_url
Play online audio URL

**Request Body:**
```json
{
  "url": "https://example.com/audio.wav",   // Audio URL
  "sample_rate": 16000                      // Target sample rate (optional)
}
```

**Response:**
```json
{
  "status": "playing",
  "url": "https://example.com/audio.wav",
  "target_sample_rate": 16000
}
```

---

## UDP Audio Stream Format

When using UDP stream reception, the sender must follow this format:

| Parameter | Value |
|-----------|-------|
| Encoding | OPUS |
| Sample Rate | 48000 Hz (configurable) |
| Channels | Mono/Stereo (configurable) |
| Protocol | RTP over UDP |
| Port | 5001 (configurable) |

**GStreamer sender pipeline example:**
```bash
gst-launch-1.0 filesrc location=audio.wav ! wavparse ! \
  opusenc ! rtpopuspay ! udpsink host=10.42.0.75 port=5001
```

---

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐
│  Client Device  │         │   Reachy Mini        │
│  (PC/Phone/etc) │         │                      │
├─────────────────┤         │  ┌────────────────┐  │
│  test_client.py │         │  │ audio_stream   │  │
│       or        │         │  │    _server.py  │  │
│     curl        │         │  │                │  │
└────────┬────────┘         │  │  FastAPI       │  │
         │                  │  │  (Port 8001)   │  │
         │ HTTP/REST        │  └────────┬───────┘  │
         ├──────────────────>           │          │
         │                  │          │          │
         │                  │  ┌───────▼───────┐  │
         │                  │  │  Audio        │  │
         │                  │  │  Player       │  │
         │                  │  └───────┬───────┘  │
         │                  │          │          │
         │                  │  ┌───────▼───────┐  │
         │                  │  │  ALSA Sink    │  │
         │                  │  │  (Speaker)    │  │
         │                  │  └───────────────┘  │
         │                  └──────────────────────┘
```

---

## Expected Output

### Server Start
```
Starting Audio Stream Service...
UDP port: 5001
Audio device: reachymini_audio_sink
API port: 8001
Listen on: 0.0.0.0:8001

API Endpoints:
  POST /stream/start    - Start UDP audio stream reception
  POST /stream/stop     - Stop audio stream reception
  GET  /stream/status   - Get current status
  POST /stream/play_url - Play audio from URL
  POST /stream/play_file - Play local file

LAN access example:
  curl http://<ROBOT_IP>:8001/stream/status

INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Client Test
```
============================================================
Reachy Mini Audio Stream Service - Client Test
============================================================
Service URL: http://10.42.0.75:8001

>>> Health check...
✅ Healthy: {"status": "healthy"}

>>> Get service status...
✅ Status: {"is_running": false}

------------------------------------------------------------
Test 1: Play local file
------------------------------------------------------------

>>> Play local file: /home/pollen/prompt_audio_1.wav
✅ Started playing: {"status": "playing", "file_path": "/home/pollen/prompt_audio_1.wav", "target_sample_rate": 16000}

============================================================
Test Complete!
============================================================
```

---

## Troubleshooting

### Issue 1: Client Connection Failed

**Error**: `❌ Connection failed: Cannot connect to http://10.42.0.75:8001`

**Solutions**:
1. Check if Reachy Mini is powered on
2. Confirm server is running (`ps aux | grep audio_stream_server`)
3. Verify IP address is correct (`ip addr show`)
4. Ensure firewall is not blocking port 8001

### Issue 2: File Not Found

**Error**: `File not found: /path/to/audio.wav`

**Solutions**:
- File path must be a local path on Reachy Mini
- Use absolute paths
- Confirm file exists and is readable

### Issue 3: UDP Stream No Sound

**Possible causes**:
- UDP port configuration mismatch
- Incorrect audio format
- Firewall blocking UDP port 5001

**Solutions**:
1. Check that sender and receiver ports match
2. Confirm audio encoding is OPUS
3. Test UDP connectivity with `nc -u 10.42.0.75 5001`

---

## Use Cases

| Scenario | Description | API / Tool |
|----------|-------------|-----|
| Remote Voice Playback | Push voice from server to robot | `/stream/play_url` |
| Local Audio Playback | Play audio stored on robot | `/stream/play_file` |
| Real-time Streaming | Low-latency real-time audio | `/stream/start` + UDP |
| Remote Speaker | Stream PC audio to robot | `stream_pc_audio.py` |
| Status Monitoring | Check if service is running | `/stream/status` |

---

## Live Streaming Details

### How It Works

```
┌─────────────────┐         ┌──────────────────────┐
│      PC         │         │   Reachy Mini        │
├─────────────────┤         │                      │
│  ┌───────────┐  │         │  ┌────────────────┐  │
│  │  System   │  │         │  │ audio_stream   │  │
│  │  Audio    │──┼───UDP──>│  │    _server.py  │  │
│  │  Output   │  │ │ 5001   │  │                │  │
│  └───────────┘  │         │  │  UDP Receiver  │  │
│       ↑         │         │  └───────┬────────┘  │
│       │         │         │          │            │
│  ┌────┴─────┐   │         │  ┌───────▼────────┐  │
│  │Stereo Mix│   │         │  │  ALSA Sink     │  │
│  │(Loopback)│   │         │  │  (Speaker)     │  │
│  └──────────┘   │         │  └────────────────┘  │
└─────────────────┘         └──────────────────────┘
```

### Streaming Parameters

| Parameter | Value |
|-----------|-------|
| Sample Rate | 48000 Hz |
| Channels | Mono |
| Encoding | PCM 16-bit |
| Protocol | UDP |
| Latency | ~20-50ms |

### Tips

1. **Best Experience**: Use loopback device (Stereo Mix) to capture all system audio
2. **Low Latency**: Script uses small buffer (960 samples @ 48kHz = 20ms)
3. **Network**: Wired network recommended, WiFi may add latency

---

## Related Documentation

- [API Reference](../../docs/API_REFERENCE_EN.md)
- [Network Configuration Guide](../../docs/NETWORK_GUIDE_EN.md)
- [Demo 07: Audio Player](../07_audio_player/)

---

## License

MIT License
