# Demo 5: Reachy Mini 音频功能演示

Reachy Mini 音频输入/输出功能演示集合，包含音频推送和麦克风录音两个功能。

---

## Part A: 音频推送 (audio_streaming.py)

将电脑的音频实时推送到 Reachy Mini 机器人进行播放，实现电脑音响与机器人语音同步的功能。

### 功能特性

- **实时音频推送**: 捕获电脑系统音频并推送到机器人播放
- **多设备支持**: 支持选择不同的音频输入设备
- **音频文件播放**: 支持直接播放 WAV 文件（用于测试）
- **参数可配置**: 支持调整采样率、声道数、缓冲区大小
- **实时可视化**: 显示音频波形和音量级别
- **自动混音**: 自动将立体声混音为单声道（如果需要）

### 快速开始

#### 1. 列出可用音频设备

```bash
python audio_streaming.py --list-devices
```

#### 2. 使用默认设备推送音频

```bash
python audio_streaming.py
```

#### 3. 指定音频设备

```bash
python audio_streaming.py --device 1
```

#### 4. 从音频文件播放（测试用）

```bash
python audio_streaming.py --file test.wav
```

### 音频设备设置

#### Windows - 启用立体声混音

1. 打开声音控制面板 → 录制选项卡
2. 右键勾选"显示已禁用的设备"
3. 启用"立体声混音"并设为默认设备
4. 运行程序

#### Mac - 使用 BlackHole

```bash
brew install blackhole-2ch
```

#### Linux - 使用 PulseAudio

```bash
sudo apt-get install pavucontrol
```

---

## Part B: 麦克风录音 (mic_recording.py)

从 Reachy Mini 的麦克风录制音频，支持实时监听、保存到文件、声源定位等功能。

### 功能特性

- **实时录音**: 从机器人麦克风获取音频流
- **实时监听**: 通过电脑扬声器实时播放录音内容
- **保存录音**: 将录音保存为 WAV 文件
- **声源定位 (DoA)**: 显示声源方向（需要麦克风阵列支持）
- **音频可视化**: 实时显示音频波形和音量
- **录音分析**: 录音结束后显示详细统计信息

### 快速开始

#### 1. 简单录音（5秒）

```bash
python mic_recording.py --simple --duration 5
```

#### 2. 录音并保存到文件

```bash
python mic_recording.py --output my_recording.wav
```

#### 3. 录音并实时监听

```bash
python mic_recording.py --monitor
```

#### 4. 录音并显示声源定位

```bash
python mic_recording.py --doa
```

#### 5. 完整功能（监听 + DoA + 保存）

```bash
python mic_recording.py --monitor --doa --output test.wav
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--simple` | 使用简单录音模式（无可视化） | - |
| `--duration` | 录音时长（秒），仅简单模式 | None（手动停止） |
| `--output`, `-o` | 输出 WAV 文件路径 | 自动生成文件名 |
| `--monitor` | 启用实时监听 | - |
| `--doa` | 启用声源定位显示 | - |
| `--no-visualizer` | 禁用音频可视化 | - |
| `--backend` | 媒体后端 | default |

### 使用场景

#### 1. 语音录制

录制机器人麦克风的声音并保存：

```bash
python mic_recording.py --output speech.wav --simple --duration 10
```

#### 2. 实时监听

实时监听机器人麦克风的声音（通过电脑扬声器）：

```bash
python mic_recording.py --monitor
```

#### 3. 声源定位追踪

结合声源定位功能，追踪说话人的方向：

```bash
python mic_recording.py --doa
```

输出示例：
```
检测到语音！方向: 前方 (12.3°)
检测到语音！方向: 左侧 (-45.6°)
```

#### 4. 语音数据收集

用于收集语音数据集：

```bash
python mic_recording.py --output voice_sample_001.wav --simple --duration 5
```

### 代码示例

#### 基础录音

```python
from reachy_mini import ReachyMini

with ReachyMini() as mini:
    # 获取音频参数
    sample_rate = mini.media.get_input_audio_samplerate()
    channels = mini.media.get_input_channels()

    print(f"采样率: {sample_rate} Hz, 声道: {channels}")

    # 开始录音
    mini.media.start_recording()

    # 录制 5 秒
    import time
    for i in range(50):
        audio_sample = mini.media.get_audio_sample()
        if audio_sample is not None:
            print(f"\r录制中... {i*0.1:.1f}s", end='')
        time.sleep(0.1)

    # 停止录音
    mini.media.stop_recording()
```

#### 声源定位

```python
from reachy_mini import ReachyMini
import math

with ReachyMini() as mini:
    while True:
        doa_result = mini.media.get_DoA()

        if doa_result is not None:
            angle, speech_detected = doa_result

            if speech_detected:
                angle_deg = math.degrees(angle)

                # 判断方向
                if -45 <= angle_deg <= 45:
                    direction = "前方"
                elif -135 <= angle_deg < -45:
                    direction = "左侧"
                elif 45 < angle_deg <= 135:
                    direction = "后方"
                else:
                    direction = "右侧"

                print(f"检测到语音！方向: {direction} ({angle_deg:.1f}°)")
```

#### 带监听的录音

```python
from reachy_mini import ReachyMini
import pyaudio
import numpy as np
import time

with ReachyMini() as mini:
    sample_rate = mini.media.get_input_audio_samplerate()
    channels = mini.media.get_input_channels()

    # 设置 PyAudio 输出流（监听）
    p = pyaudio.PyAudio()
    monitor_stream = p.open(
        format=pyaudio.paFloat32,
        channels=channels,
        rate=sample_rate,
        output=True
    )

    # 开始录音
    mini.media.start_recording()

    try:
        while True:
            # 获取音频样本
            audio_sample = mini.media.get_audio_sample()

            if audio_sample is not None:
                # 播放到电脑扬声器（监听）
                monitor_stream.write(audio_sample.tobytes())

                # 可选：处理音频数据
                # ...
    except KeyboardInterrupt:
        pass
    finally:
        mini.media.stop_recording()
        monitor_stream.close()
        p.terminate()
```

---

## 工作原理

### 音频推送流程

```
┌─────────────────┐
│   电脑音频源    │
│ (音乐/视频/系统)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  立体声混音/    │
│  虚拟音频设备   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PyAudio 捕获   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  音频处理       │
│ (归一化/混音)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Reachy Mini     │
│ push_audio_sample│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  机器人扬声器   │
└─────────────────┘
```

### 麦克风录音流程

```
┌─────────────────┐
│ Reachy Mini     │
│   麦克风阵列    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ start_recording │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ get_audio_sample│ ← 循环获取
└────────┬────────┘
         │
         ├──▶ ┌─────────────┐
         │    │  实时监听    │ (可选)
         │    └─────────────┘
         │
         ├──▶ ┌─────────────┐
         │    │  声源定位    │ (可选)
         │    └─────────────┘
         │
         ├──▶ ┌─────────────┐
         │    │  保存文件    │ (可选)
         │    └─────────────┘
         │
         ▼
┌─────────────────┐
│ stop_recording  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   录音分析      │
└─────────────────┘
```

---

## 依赖

### 通用依赖

```bash
pip install reachy-mini numpy
```

### 音频推送依赖

```bash
pip install pyaudio scipy
```

### 麦克风录音依赖

```bash
# 必需
pip install reachy-mini numpy

# 可选（用于监听功能）
pip install pyaudio

# 可选（用于保存 WAV 文件）
pip install scipy
```

### PyAudio 安装说明

- **Windows**: `pip install pipwin && pipwin install pyaudio`
- **Mac**: `brew install portaudio && pip install pyaudio`
- **Linux**: `sudo apt-get install python3-pyaudio`

---

## 常见问题

### 音频推送

**Q: 听不到声音？**
A:
1. 检查是否正确启用了立体声混音设备
2. 确认选择的音频设备正确（使用 `--list-devices`）
3. 测试立体声混音是否工作
4. 检查机器人音量设置

**Q: 音频卡顿/断续？**
A:
1. 增加缓冲区大小：`--buffer-size 2048` 或 `4096`
2. 关闭其他占用 CPU 的程序
3. 检查网络连接

### 麦克风录音

**Q: 录音没有声音？**
A:
1. 确认机器人麦克风已连接
2. 检查 daemon 服务是否运行
3. 尝试使用 `--simple` 模式测试
4. 检查采样率设置

**Q: 监听功能不工作？**
A:
1. 确认已安装 PyAudio
2. 检查电脑扬声器是否正常工作
3. 尝试不同的 `--backend` 参数

**Q: 声源定位不显示？**
A:
1. 确认机器人配备麦克风阵列（如 ReSpeaker）
2. 使用 `--doa` 参数启用
3. 声源定位仅在检测到语音时显示

---

## 注意事项

1. 确保 Reachy Mini 的 daemon 服务已启动
2. 音频推送需要正确配置虚拟音频设备
3. 推送音频时避免同时使用机器人的其他音频功能
4. 如果是网络连接的机器人，确保网络稳定
5. 长时间录音会产生大量数据，注意磁盘空间
