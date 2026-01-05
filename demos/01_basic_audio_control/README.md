# Demo 01: 基础音频控制

通过 HTTP REST API 控制 Reachy Mini 机器人的扬声器音量和麦克风增益。

---

## 运行平台

| 平台 | 支持情况 |
|------|----------|
| PC   | ✅ 支持 |
| Reachy Mini | ❌ 不适用 |

> 此 demo 在 PC 上运行，通过网络控制 Reachy Mini 的音频功能。

---

## 功能特性

- 获取和设置扬声器音量 (0-100%)
- 获取和设置麦克风增益 (0-100%)
- 播放测试音验证音频输出

---

## 前置条件

### 1. 系统要求

- **操作系统**: Linux, macOS, Windows
- **Python**: 3.7+
- **网络**: 与 Reachy Mini 在同一局域网

### 2. Python 依赖

```bash
pip install requests
# 或使用 uv
uv pip install requests
```

---

## 使用方法

### 1. 配置连接

在 `demos` 目录下创建配置文件：

```bash
cd demos
cp robot_config.yaml.template robot_config.yaml
# 编辑 robot_config.yaml，设置 Reachy Mini 的 IP 地址
```

### 2. 运行脚本

```bash
cd demos/01_basic_audio_control
python3 test_audio_control.py
```

---

## 脚本说明

### ReachyMiniAudioClient 类

提供以下方法：

| 方法 | 说明 |
|------|------|
| `get_speaker_volume()` | 获取当前扬声器音量 |
| `set_speaker_volume(volume)` | 设置扬声器音量 (0-100) |
| `play_test_sound()` | 播放测试音 |
| `get_microphone_volume()` | 获取当前麦克风增益 |
| `set_microphone_volume(volume)` | 设置麦克风增益 (0-100) |

---

## API 接口

此 demo 使用以下 REST API：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/volume/current` | GET | 获取扬声器音量 |
| `/api/volume/set` | POST | 设置扬声器音量 |
| `/api/volume/test-sound` | POST | 播放测试音 |
| `/api/volume/microphone/current` | GET | 获取麦克风增益 |
| `/api/volume/microphone/set` | POST | 设置麦克风增益 |

---

## 预期输出

```
==================================================
Reachy Mini 音频控制
==================================================
✅ 成功连接到 Reachy Mini: http://10.42.0.75:5000

----- 扬声器控制 -----
当前扬声器音量: 50%

设置音量为 80%...
设置结果: {'status': 'ok', 'volume': 50}

🔊 播放测试音...
播放结果: {'status': 'ok'}

----- 麦克风控制 -----
当前麦克风增益: 50%

设置麦克风增益为 70%...
设置结果: {'status': 'ok', 'volume': 70}

==================================================
完成!
==================================================
```

---

## 故障排除

### 问题 1: 连接失败

**原因**: 无法连接到 Reachy Mini

**解决**:
- 检查 Reachy Mini 是否开机
- 检查网络连接
- 确认 `robot_config.yaml` 中的 IP 地址正确

### 问题 2: 无声音输出

**原因**: 扬声器音量设置过低或静音

**解决**:
- 使用 `set_speaker_volume(100)` 设置最大音量
- 运行 `play_test_sound()` 测试音频

---

## 相关文档

- [API 参考文档](../../docs/API_REFERENCE_CN.md)
- [网络配置指南](../../docs/NETWORK_GUIDE_CN.md)
- [使用指南](../../docs/USAGE_GUIDE_CN.md)

---

## 许可证

MIT License
