# 🤖 Demo 11: YOLO 目标检测 + Zenoh 机器人控制

基于 WebRTC 视频流运行 YOLO 目标检测，并通过 Zenoh 协议实时控制 Reachy Mini 机器人身体运动。

---

## 运行平台

| 平台 | 支持情况 |
|------|----------|
| PC   | ✅ 支持 |
| Reachy Mini | ❌ 不适用 |

> 此 demo 在 PC 上运行，接收视频流并通过 Zenoh 控制 Reachy Mini。

---

## 功能特性

- **YOLOv8 目标检测**: 实时检测 80+ 种物体
- **Zenoh 低延迟控制**: 使用 Zenoh 协议实现超低延迟机器人控制
- **键盘控制**: WASD 键盘控制机器人身体旋转
- **实时视频**: WebRTC 视频流显示检测结果

---

## 前置条件

### 1. 系统要求

- **操作系统**: Linux (Ubuntu 20.04/22.04)
- **Python**: 3.7+
- **网络**: 与 Reachy Mini 在同一局域网
- **配置文件**: 需要 `robot_config.yaml` (参考 Demo 06)

### 2. 依赖安装

```bash
# Python 依赖
pip install opencv-python numpy ultralytics zenoh

# Reachy Mini (含 GStreamer)
pip install 'reachy-mini[gstreamer]'
```

### 3. 配置文件

在项目根目录创建 `robot_config.yaml`:

```yaml
# Reachy Mini 机器人配置
robot_ip: "10.42.0.75"  # 修改为你的 Reachy Mini IP 地址
```

---

## 使用方法

### 基本用法

```bash
# 使用默认配置
python3 11.py

# 指定视频流地址
python3 11.py --signaling-host 10.42.0.75

# 完整配置
python3 11.py -s 10.42.0.75 -p 8443 -n reachymini
```

### 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--signaling-host` | `-s` | `127.0.0.1` | 视频流信令服务器地址 |
| `--signaling-port` | `-p` | `8443` | 视频流信令服务器端口 |
| `--peer-name` | `-n` | `reachymini` | 对等体名称 |

### 键盘控制

| 按键 | 功能 |
|------|------|
| `A` | 向左旋转身体 (Yaw +) |
| `D` | 向右旋转身体 (Yaw -) |
| `S` | 回正 (Yaw = 0) |
| `Q` | 退出程序 |

---

## 工作原理

```
┌─────────────────────────────────────────────────────────────────┐
│                         PC 端                                  │
│                                                                  │
│  ┌─────────────┐         ┌─────────────┐                       │
│  │ WebRTC      │         │  YOLOv8     │                       │
│  │ 视频流      │────────►│  目标检测   │                       │
│  └─────────────┘         └─────────────┘                       │
│                                  │                               │
│                                  ▼                               │
│  ┌──────────────────────────────────────────┐                   │
│  │         OpenCV 显示窗口                  │                   │
│  │   (显示检测结果 + 当前角度)              │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                  │
│  ┌─────────────┐                                              │
│  │   键盘输入   │ (A/D/S)                                     │
│  └──────┬──────┘                                              │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐         Zenoh (TCP/7447)      ┌───────────┐  │
│  │ Zenoh       │ ═════════════════════════════►│ Reachy    │  │
│  │ Publisher   │                            │ Mini      │  │
│  └─────────────┘                            │ 机器人    │  │
│                                             └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

1. **视频接收**: 通过 WebRTC 接收 Reachy Mini 的视频流
2. **YOLO 检测**: 对每帧运行 YOLOv8 检测
3. **结果显示**: 在 OpenCV 窗口显示检测结果和当前角度
4. **Zenoh 控制**: 键盘输入通过 Zenoh 发送控制指令

---

## 故障排除

### 问题 1: `ImportError: No module named 'zenoh'`

**解决**:
```bash
pip install zenoh
```

### 问题 2: `ImportError: No module named 'ultralytics'`

**解决**:
```bash
pip install ultralytics
```

### 问题 3: Zenoh 连接失败

**原因**: 配置文件中 robot_ip 不正确

**解决**: 检查 `robot_config.yaml` 中的 IP 地址

### 问题 4: 机器人不响应

**检查**:
1. Reachy Mini 是否运行 Zenoh 服务
2. 配置文件 IP 是否正确
3. 网络连接是否正常

---

## 性能参考

| 项目 | 数值 |
|------|------|
| YOLOv8n 推理速度 (CPU) | ~30-50ms |
| Zenoh 控制延迟 | <5ms |
| 总体系统延迟 | <100ms |

> 测试环境: Ubuntu 22.04, Intel i5-1135G7

---

## 相关文档

- [Demo 06: Zenoh 基础控制](../06_zenoh_basic_control/README.md)
- [Demo 10: 视觉算法演示](../10_vision_algorithms/README.md)
- [YOLOv8 文档](https://docs.ultralytics.com/)
- [Zenoh Python API](https://zenoh.io/docs/manual/getting-started/python/)

---

## 许可证

MIT License
