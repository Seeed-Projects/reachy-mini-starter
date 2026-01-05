# Demo 02: 基础底座旋转

控制 Reachy Mini 机器人的底座左右旋转运动。

---

## 运行平台

| 平台 | 支持情况 |
|------|----------|
| PC   | ✅ 支持 |
| Reachy Mini | ❌ 不适用 |

> 此 demo 在 PC 上运行，通过网络控制 Reachy Mini 的运动。

---

## 功能特性

- 底座左右旋转 (body_yaw 控制)
- 可配置旋转次数
- 平滑插值运动 (minjerk)

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
cd demos/02_basic_body_rotation
python3 test_body_rotation.py
```

默认会旋转 3 次，可以通过修改代码调整次数：

```python
rotate_base(count=5)  # 旋转 5 次
```

---

## 运动参数

### body_yaw (底座偏航)

| 参数 | 说明 |
|------|------|
| 控制轴 | 底座水平旋转 |
| 角度范围 | ±160 度 |
| 正值 | 向左转 |
| 负值 | 向右转 |

---

## API 接口

此 demo 使用以下 REST API：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/motors/set_mode/enabled` | POST | 启用电机 |
| `/api/move/goto` | POST | 控制机器人运动 |

### 运动请求格式

```json
{
  "body_yaw": 30,           // 底座偏航角度 (度)
  "duration": 1.0,          // 运动持续时间 (秒)
  "interpolation": "minjerk" // 插值方式
}
```

---

## 预期输出

```
==================================================
Reachy Mini 底座旋转演示
==================================================

启用电机...

🔄 底座旋转 3 次...
  第 1 次: 左转 -> 右转
  第 2 次: 左转 -> 右转
  第 3 次: 左转 -> 右转

回到原位...

==================================================
完成!
==================================================
```

---

## 运动说明

脚本执行以下动作序列：

1. 启用电机
2. 重复指定次数：
   - 底座左转 30 度 (1秒)
   - 底座右转 -30 度 (1秒)
3. 回到原位 (0度)

---

## 故障排除

### 问题 1: 机器人不动

**原因**: 电机未启用

**解决**: 脚本会自动启用电机，如果仍不动请检查：
- Reachy Mini 是否开机
- 网络连接是否正常
- 检查机器人是否有错误提示

### 问题 2: 运动不平滑

**原因**: duration 设置过小

**解决**: 增加运动持续时间：
```python
"duration": 2.0,  # 改为 2 秒
```

---

## 相关文档

- [API 参考文档](../../docs/API_REFERENCE_CN.md)
- [运动控制说明](../../docs/USAGE_GUIDE_CN.md)
- [网络配置指南](../../docs/NETWORK_GUIDE_CN.md)

---

## 许可证

MIT License
