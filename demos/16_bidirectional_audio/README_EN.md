# Demo 16: Bidirectional Audio Service

Establish bidirectional audio connection between Reachy Mini and PC via WebSocket:
- **Uplink**: Reachy Mini Microphone → PC (Remote Monitoring)
- **Downlink**: PC → Reachy Mini Audio Playback

---

## Platform Support

| Platform | Support |
|----------|---------|
| PC   | ✅ Client |
| Reachy Mini | ✅ Server |

> This demo has two parts:
> - **Server** - Runs on Reachy Mini, provides audio streaming and playback
> - **Client** - Runs on any device in the LAN, receives microphone stream

---

## Features

### Server (Reachy Mini)
- **Real-time Mic Streaming** - Stream microphone audio via WebSocket
- **Multi-client Support** - Multiple PCs can connect simultaneously
- **File Playback** - Remote playback of local audio files
- **Auto Management** - Auto-start capture on client connect, auto-stop when idle

### Client (PC)
- **Real-time Reception** - Receive and play Reachy Mini microphone audio
- **Low Latency** - Real-time decoding with ffplay
- **Cross-platform** - Supports Windows, macOS, Linux

---

## Prerequisites

### 1. System Requirements

- **Server**: Reachy Mini (Linux)
- **Client**: Any device with Python support
- **Network**: Devices on the same LAN

### 2. Server Dependencies (Reachy Mini)

```bash
# Python packages
pip install fastapi uvicorn pydantic gobject

# Or use system package manager
sudo apt install python3-gi python3-gi-cairo gstreamer1.0-python3-plugin-loader
```

### 3. Client Dependencies (PC)

```bash
# Python dependency
pip install websocket-client

# ffplay player

# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

---

## Usage

### Step 1: Start Server (Reachy Mini)

```bash
cd demos/16_bidirectional_audio
python3 bidirectional_audio_server.py
```

Service will listen on `0.0.0.0:8002`, accessible from any device in the LAN.

**Expected output:**
```
============================================================
Reachy Mini Bidirectional Audio Service
============================================================
Audio output device: reachymini_audio_sink
Audio input device: reachymini_audio_src
Mic sample rate: 16000 Hz
============================================================

INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     🚀 Bidirectional audio service ready
INFO:     Listen address: 0.0.0.0:8002
INFO:     Mic WebSocket: ws://<IP>:8002/audio/mic
INFO:     Play API: POST http://<IP>:8002/stream/play_file
```

---

### Step 2: Start Client (PC)

#### Method 1: Receive Mic Stream (Remote Monitoring) ⭐

**Main feature** - Turn Reachy Mini into a remote monitoring device!

**How it works:**
1. PC connects to Reachy Mini's WebSocket service
2. Reachy Mini starts capturing microphone audio
3. Stream to PC in real-time and play
4. You can hear sounds around Reachy Mini

**Usage:**

```bash
# Use default IP
python3 receive_mic_stream.py

# Specify robot IP
python3 receive_mic_stream.py --robot-ip 10.42.0.75

# Specify port
python3 receive_mic_stream.py --robot-ip 10.42.0.75 --port 8002

# Show ffplay window (debug)
python3 receive_mic_stream.py --robot-ip 10.42.0.75 --show-window
```

**Expected output:**
```
============================================================
Reachy Mini Mic Stream Receiver
============================================================
Target robot: 10.42.0.75
Port: 8002
Audio format: OPUS
Sample rate: 16000 Hz
Channels: 1
============================================================

Connecting to ws://10.42.0.75:8002/audio/mic
✅ Connected to Reachy Mini microphone
Listening on ws://10.42.0.75:8002/audio/mic
Press Ctrl+C to stop

  Received: 125.3 KB (25.1 KB/s)
```

#### Method 2: Remote Audio File Playback

```bash
# Play audio file on Reachy Mini
curl -X POST http://10.42.0.75:8002/stream/play_file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/home/pollen/audio.wav"}'
```

#### Method 3: Multi-client Monitoring

Run client on multiple PCs, all receive microphone stream:

```bash
# PC 1
python3 receive_mic_stream.py --robot-ip 10.42.0.75

# PC 2
python3 receive_mic_stream.py --robot-ip 10.42.0.75

# PC 3
python3 receive_mic_stream.py --robot-ip 10.42.0.75
```

---

## API Endpoints

### WebSocket Endpoints

#### WS /audio/mic
Microphone audio stream endpoint

**Connection example:**
```python
import websocket

ws = websocket.WebSocketApp(
    "ws://10.42.0.75:8002/audio/mic",
    on_message=lambda ws, msg: print(f"Received {len(msg)} bytes")
)
ws.run_forever()
```

### HTTP Endpoints

#### GET /
Service information

**Response:**
```json
{
  "service": "Reachy Mini Bidirectional Audio Service",
  "version": "1.0.0",
  "endpoints": {
    "websocket": "ws://<IP>:8002/audio/mic",
    "play_file": "POST http://<IP>:8002/stream/play_file"
  }
}
```

#### GET /health
Health check

**Response:**
```json
{
  "status": "healthy",
  "mic_clients": 2
}
```

#### GET /status
Get detailed status

**Response:**
```json
{
  "service": "bidirectional_audio",
  "mic_forwarding": true,
  "mic_clients": 2,
  "audio_device": "reachymini_audio_src"
}
```

#### POST /stream/play_file
Play local audio file

**Request body:**
```json
{
  "file_path": "/path/to/audio.wav"
}
```

**Response:**
```json
{
  "status": "playing",
  "file": "/path/to/audio.wav",
  "message": "Starting audio playback"
}
```

---

## How It Works

### Audio Stream Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Reachy Mini Side                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Mic → ALSA → GStreamer → Opus Enc → WebSocket     │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ WebSocket (Opus)
                            │ (Port 8002)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                         PC Side                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  WebSocket → Receive Opus → ffplay Decode → Speaker │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Audio Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Sample Rate | 16000 Hz | Voice quality |
| Channels | Mono (1) | Best compatibility |
| Encoding | Opus (32kbps) | High compression, low latency |
| Protocol | WebSocket | Bidirectional |
| Port | 8002 | Configurable |
| Latency | ~50-100ms | Network dependent |

### Auto Management

1. **First client connects** - Auto-start GStreamer mic capture
2. **Client disconnects** - Auto-remove disconnected connection
3. **All clients gone** - Auto-stop capture to save resources
4. **New client connects** - Auto-resume capture

---

## Use Cases

| Scenario | Description | Usage |
|----------|-------------|-------|
| **Remote Monitoring** ⭐ | Monitor sounds around Reachy Mini | `receive_mic_stream.py` |
| Voice Interaction | Real-time voice communication | Combine with speech recognition |
| Multi-point Monitoring | Multiple locations monitor simultaneously | Multiple clients |
| Remote Playback | Play audio on Reachy Mini | `POST /stream/play_file` |

---

## Troubleshooting

### Issue 1: Client Connection Failed

**Error**: `❌ Connection failed: Cannot connect to ws://10.42.0.75:8002/audio/mic`

**Solutions**:
1. Check if Reachy Mini is powered on
2. Confirm server is running (`ps aux | grep bidirectional_audio_server`)
3. Verify IP address is correct
4. Ensure firewall is not blocking port 8002

### Issue 2: ffplay Not Found

**Error**: `ffplay command not found`

**Solutions**:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Verify installation
ffplay -version
```

### Issue 3: No Audio Output

**Possible causes**:
- ffplay parameters mismatch
- Audio device issue
- Microphone not capturing

**Solutions**:
1. Use `--show-window` to check if audio waveform is visible
2. Check system volume settings
3. Confirm Reachy Mini mic device is correct (`reachymini_audio_src`)

### Issue 4: Audio Stuttering

**Solutions**:
1. Use wired network instead of WiFi
2. Check network signal strength
3. Ensure sufficient bandwidth (Opus 32kbps is very low)

---

## Files

| File | Description | Platform |
|------|-------------|----------|
| `bidirectional_audio_server.py` | Bidirectional audio server | Reachy Mini |
| `receive_mic_stream.py` | Mic stream receiver client | PC |

---

## Relationship with Other Demos

| Demo | Function | Relationship |
|------|----------|--------------|
| **Demo 08** | PC audio → Reachy Mini | Reverse data flow |
| **Demo 09** | Reachy Mini mic → PC | Forward data flow |

**Combined**: Demo 08 + Demo 09 = Complete bidirectional real-time audio communication

---

## Advanced Usage

### Integrate with Speech Recognition

```python
import websocket

def on_message(ws, message):
    # Pass Opus data to speech recognition service
    # ...

ws = websocket.WebSocketApp(
    "ws://10.42.0.75:8002/audio/mic",
    on_message=on_message
)
ws.run_forever()
```

### Save Audio Stream

```bash
# Save to file using pipe
python3 receive_mic_stream.py --robot-ip 10.42.0.75 | \
  ffmpeg -f opus -ac 1 -ar 16000 -i - output.wav
```

---

## Related Documentation

- [Demo 08: Audio Stream API](../08_audio_stream_api/)
- [Demo 05: WebRTC Video Stream](../05_webrtc_video_stream/)
- [API Reference](../../docs/API_REFERENCE_EN.md)
- [Network Configuration Guide](../../docs/NETWORK_GUIDE_EN.md)

---

## License

MIT License
