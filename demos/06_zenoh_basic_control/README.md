# Demo 06: Zenoh 基础控制

使用 Zenoh 协议控制 Reachy Mini 机器人的运动和电机状态。

---

## 运行平台

| 平台 | 支持情况 |
|------|----------|
| PC   | ✅ 支持 |
| Reachy Mini | ❌ 不适用 |

> 此 demo 在 PC 上运行，通过 Zenoh 协议控制 Reachy Mini。

---

## 关于 Zenoh

Zenoh 是一个高性能的数据传输协议，相比 REST API 具有以下优势：

- **低延迟**: 点对点直连，无需 HTTP 开销
- **高吞吐**: 二进制协议，传输效率更高
- **实时性**: 支持亚毫秒级响应
- **轻量级**: 适合边缘计算和物联网场景

---

## 功能特性

- 电机扭矩控制 (开启/关闭)
- 天线运动控制 (左右独立)
- 底座旋转控制 (body_yaw)
- 头部姿态控制 (pitch/yaw/roll)
- 平滑运动和归位

---

## 前置条件

### 1. 系统要求

- **操作系统**: Linux, macOS, Windows
- **Python**: 3.7+
- **网络**: 与 Reachy Mini 在同一局域网

### 2. Python 依赖

```bash
pip install zenoh
# 或使用 uv
uv pip install zenoh
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
cd demos/06_zenoh_basic_control
python3 test_zenoh_control.py
```

---

## Zenoh 协议说明

### 连接配置

```python
# Zenoh 连接端点
endpoint = "tcp/{ROBOT_IP}:7447"

# 命令话题
topic = "reachy_mini/command"
```

### 支持的命令

| 命令 | 格式 | 说明 |
|------|------|------|
| 电机扭矩 | `{"torque": bool, "ids": list\|None}` | 开启/关闭电机 |
| 天线位置 | `{"antennas_joint_positions": [左, 右]}` | 天线角度 (弧度) |
| 底座偏航 | `{"body_yaw": float}` | 底座旋转角度 (弧度) |
| 头部姿态 | `{"head_pose": {"pitch": float, "yaw": float, "roll": float}}` | 头部姿态 |

---

## 预期输出

```
==================================================
Reachy Mini Zenoh 控制
==================================================

配置信息:
  机器人 IP: 10.42.0.75
  Zenoh 端口: 7447
  命令话题: reachy_mini/command

正在连接到机器人: tcp/10.42.0.75:7447 ...
✅ Zenoh Session 建立成功！
📢 已建立指令通道: reachy_mini/command

>>> [1/5] 发送指令: 开启电机 (Torque ON)
>>> [2/5] 发送指令: 移动天线 (左歪)
>>> [2/5] 发送指令: 移动天线 (右歪)
>>> [3/5] 发送指令: 旋转身体 (左转)
>>> [3/5] 发送指令: 旋转身体 (回正)
>>> [4/5] 发送指令: 点头
>>> [5/5] 发送指令: 全部归零

==================================================
完成!
==================================================
>>> 放松电机
🔌 连接已断开
```

---

## 运动序列

脚本执行以下动作序列：

1. **开启电机** - 启用所有电机扭矩
2. **天线运动** - 左歪 / 右歪
3. **底座旋转** - 左转 30度 / 回正
4. **点头动作** - 低头 / 抬头
5. **归位放松** - 所有关节回零并放松电机

---

## 角度说明

### 弧度与角度转换

| 关节 | 弧度 | 角度 |
|------|------|------|
| 天线 | ±0.5 | ±30° |
| 底座 | ±0.5 | ±30° |
| 头部俯仰 | ±0.15 | ±9° |

转换公式：
```python
角度 = 弧度 × 180 / π
弧度 = 角度 × π / 180
```

---

## 故障排除

### 问题 1: 连接失败

**原因**: 无法连接到 Zenoh 端口

**解决**:
- 检查 Reachy Mini 是否开机
- 检查网络连接
- 确认 IP 地址正确
- 确认端口 7447 未被防火墙阻止

### 问题 2: 导入 zenoh 失败

**原因**: 未安装 zenoh-python

**解决**:
```bash
pip install zenoh
```

### 问题 3: 机器人不动

**原因**: 电机未开启

**解决**: 确保先发送开启扭矩指令：
```python
cmd_torque = {"torque": True, "ids": None}
```

---

## Zenoh vs REST API

| 特性 | Zenoh | REST API |
|------|-------|----------|
| 延迟 | 低 (~1ms) | 高 (~10-50ms) |
| 吞吐 | 高 | 中 |
| 协议 | TCP + 二进制 | HTTP + JSON |
| 适用场景 | 实时控制 | 简单操作 |

---

## 相关文档

- [Zenoh 官方文档](https://zenoh.io/)
- [API 参考文档](../../docs/API_REFERENCE_CN.md)
- [网络配置指南](../../docs/NETWORK_GUIDE_CN.md)

---

## 许可证

MIT License
