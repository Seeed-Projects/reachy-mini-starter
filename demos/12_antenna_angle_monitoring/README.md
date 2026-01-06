# Demo 12: 天线角度实时监控

本演示展示如何使用 REST API 获取 Reachy Mini 机器人天线舵机的实时角度。

## 功能说明

通过 REST API 查询天线舵机的当前角度位置，支持：
- 单次查询获取当前角度
- 持续监控角度变化
- 弧度和度数两种单位显示
- 可视化角度显示

## 文件列表

| 文件 | 说明 | 通信方式 | 延迟 |
|------|------|---------|------|
| [test_antenna_rest.py](test_antenna_rest.py) | REST API 查询天线角度 | HTTP | 20-50ms |

---

## 快速开始

### 前置条件

1. 确保 Reachy Mini 机器人已开机并连接到网络
2. **配置机器人 IP 地址**：
   ```bash
   # 复制配置模板
   cp ../robot_config.yaml.template ../robot_config.yaml

   # 编辑配置文件，修改机器人 IP 地址
   vim ../robot_config.yaml
   ```
3. 安装依赖：

```bash
pip install requests
```

### 运行 Demo

```bash
python test_antenna_rest.py
```

**特点**：
- 单次查询，适合低频状态获取
- 无需额外配置
- 可设置查询间隔

**适用场景**：配置查询、状态检查、非实时应用

---

## API 参考

### REST API 端点

| 端点 | 方法 | 返回 |
|------|------|------|
| `/api/state/present_antenna_joint_positions` | GET | `[左天线弧度, 右天线弧度]` |
| `/api/state/full` | GET | 完整状态（含 `antennas_position`） |

### 测试接口

```bash
# 测试获取天线角度
curl http://<机器人IP>:8000/api/state/present_antenna_joint_positions

# 测试完整状态
curl http://<机器人IP>:8000/api/state/full

# 格式化输出
curl http://<机器人IP>:8000/api/state/full | python -m json.tool
```

---

## 使用示例

### 单次查询

```python
import requests
from pathlib import Path
import sys

# 导入配置
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config

config = get_config()

# 获取天线角度
response = requests.get(f"{config.base_url}/state/present_antenna_joint_positions")
angles_rad = response.json()

# 转换为度数
left_deg = angles_rad[0] * 180 / 3.14159
right_deg = angles_rad[1] * 180 / 3.14159

print(f"左天线: {left_deg:.1f}°")
print(f"右天线: {right_deg:.1f}°")
```

### 持续监控

```python
import requests
import time
from pathlib import Path
import sys

# 导入配置
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config

config = get_config()

# 每秒查询一次
while True:
    response = requests.get(f"{config.base_url}/state/present_antenna_joint_positions")
    angles = response.json()
    print(f"左: {angles[0]:.2f} rad, 右: {angles[1]:.2f} rad")
    time.sleep(1)
```

---

## 天线角度范围

| 参数 | 范围 | 单位 |
|------|------|------|
| 左天线 | -80 ~ +80 | 度 |
| 右天线 | -80 ~ +80 | 度 |
| 弧度范围 | ±1.40 | 弧度 |

---

## 故障排除

### 连接失败

1. 检查机器人是否开机
2. 确保已配置机器人 IP 地址：
   ```bash
   cat ../robot_config.yaml
   ```
3. 检查网络连接：`ping <机器人IP>`
4. 检查防火墙设置

### 数据不更新

1. 检查机器人电机是否启用
2. 尝试手动移动天线，观察数值变化
3. 检查控制台是否有错误消息

---

## 相关文档

- [API 参考文档](../../docs/API_REFERENCE_CN.md)
- [使用指南](../../docs/USAGE_GUIDE_CN.md)
