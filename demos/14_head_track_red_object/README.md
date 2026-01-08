# Demo 14: 红色物体追踪

使用 Reachy Mini SDK 在机器人本体上运行，结合 OpenCV 视觉追踪红色物体（螺丝刀）。

---

## 运行平台

| 平台 | 支持情况 |
|------|----------|
| PC | ❌ 不适用 |
| Reachy Mini | ✅ 支持 |

> 此 demo 需要在 Reachy Mini 机器人本体上运行，使用本地 SDK 控制和摄像头。

---

## 功能特性

**视觉追踪与头部控制结合：**
1. **摄像头捕获** - 使用 USB 摄像头实时获取视频流
2. **红色检测** - 使用 OpenCV HSV 颜色空间检测红色物体
3. **位置计算** - 计算物体在视野中的位置
4. **头部控制** - 根据物体位置控制头部转动（yaw, pitch）
5. **保持居中** - 通过反馈控制保持物体在视野中央

---

## 前置条件

### 1. 硬件要求

- **运行平台**: Reachy Mini 机器人本体
- **Python**: 3.7+
- **SDK**: reachy_mini
- **摄像头**: USB 摄像头（连接到 Reachy Mini）
- **红色物体**: 红色螺丝刀或其他红色物体

### 2. Python 依赖

```bash
# Reachy Mini SDK（通常已预装）
pip install reachy-mini

# OpenCV
pip install opencv-python

# NumPy（通常已预装）
pip install numpy
```

---

## 使用方法

### 1. 将代码传输到 Reachy Mini

```bash
# 方法 1: 使用 scp
scp demos/14_head_track_red_object/track_red_screwdriver.py reachy@10.42.0.75:/home/reachy/

# 方法 2: 使用 USB 存储设备

# 方法 3: SSH 连接后直接创建
ssh reachy@10.42.0.75
```

### 2. 连接摄像头

确保 USB 摄像头已连接到 Reachy Mini。检查摄像头设备：

```bash
# 查看摄像头设备
ls /dev/video*

# 测试摄像头
# （如果需要配置显示，可以使用 vlc 或 ffplay）
```

### 3. 在 Reachy Mini 上运行脚本

```bash
# SSH 连接到 Reachy Mini
ssh reachy@10.42.0.75

# 进入脚本所在目录
cd /home/reachy

# 运行脚本
python3 track_red_screwdriver.py
```

---

## 脚本说明

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `duration` | 追踪时长（秒） | 60 |
| `show_preview` | 是否显示预览窗口 | True |

### 控制参数

在 `RedObjectTracker` 类中可以调整：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `yaw_limit` | 左右转动最大角度 | 30° |
| `pitch_limit` | 上下转动最大角度 | 20° |
| `deadzone` | 死区比例（中心区域不移动） | 0.15 (15%) |
| `gain` | 控制增益（响应速度） | 0.8 |

### HSV 颜色范围

红色在 HSV 空间有两个范围：
- 范围 1: H[0-10], S[120-255], V[70-255]
- 范围 2: H[170-180], S[120-255], V[70-255]

如果检测效果不好，可以调整这些范围。

---

## 工作原理

### 1. 颜色检测

```python
# 转换到 HSV 颜色空间
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# 创建红色掩码
mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
mask = cv2.bitwise_or(mask1, mask2)

# 查找轮廓
contours = cv2.findContours(mask, ...)
```

### 2. 位置计算

```python
# 计算物体相对于图像中心的偏移
offset_x = (obj_x - frame_width / 2) / (frame_width / 2)
offset_y = (obj_y - frame_height / 2) / (frame_height / 2)
```

### 3. 头部控制

```python
# 计算目标角度
target_yaw = offset_x * yaw_limit * gain
target_pitch = offset_y * pitch_limit * gain

# 控制头部
mini.goto_target(
    head=create_head_pose(
        yaw=target_yaw,
        pitch=target_pitch
    ),
    duration=0.1,
    method="minjerk"
)
```

---

## 预期输出

```
============================================================
🤖 Reachy Mini 红色物体追踪演示
============================================================

📋 功能说明:
  - 使用摄像头检测红色螺丝刀
  - 根据物体位置控制头部转动
  - 保持物体在视野中央

⚠️  请将红色螺丝刀放在摄像头前
============================================================

✅ 摄像头 0 已打开
   分辨率: 640x480

🔌 连接到 Reachy Mini...
✅ 连接成功!

🎯 开始追踪（持续 60 秒）...
   按 'q' 键退出

============================================================
🎉 追踪完成!
   总帧数: 1200
   平均帧率: 20.0 FPS
============================================================
🔄 回到正中...

============================================================
演示结束!
============================================================
```

---

## 调试技巧

### 1. 颜色检测调试

如果检测不到红色物体，可以尝试：

```python
# 调整 HSV 范围
self.lower_red1 = np.array([0, 100, 50])   # 降低饱和度和亮度要求
self.upper_red1 = np.array([10, 255, 255])

# 或者显示掩码图像来调试
cv2.imshow('Mask', mask)
```

### 2. 摄像头问题

```bash
# 检查摄像头是否被占用
ls -l /dev/video0

# 测试摄像头
ffplay /dev/video0
# 或
vlc v4l2:///dev/video0
```

### 3. 性能优化

如果帧率太低：

```python
# 降低分辨率
self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# 减少处理频率
if frame_count % 2 == 0:  # 每隔一帧处理
    # 处理...
```

---

## 故障排除

### 问题 1: 摄像头无法打开

**错误**: `RuntimeError: 无法打开摄像头 0`

**解决**:
- 检查摄像头连接
- 尝试其他摄像头 ID（0, 1, 2...）
- 检查权限：`sudo usermod -a -G video reachy`

### 问题 2: 检测不到红色物体

**原因**: 光照条件、颜色范围

**解决**:
- 确保光照充足
- 调整 HSV 颜色范围
- 使用更鲜艳的红色物体

### 问题 3: 头部晃动剧烈

**原因**: 增益太大、死区太小

**解决**:
```python
self.gain = 0.5        # 降低增益
self.deadzone = 0.2    # 增大死区
```

---

## 扩展功能

### 1. 追踪其他颜色

修改 HSV 范围即可追踪其他颜色：

```python
# 绿色
self.lower_green = np.array([40, 50, 50])
self.upper_green = np.array([80, 255, 255])

# 蓝色
self.lower_blue = np.array([100, 50, 50])
self.upper_blue = np.array([130, 255, 255])
```

### 2. 多物体追踪

使用 `cv2.findContours` 找到多个轮廓，分别追踪。

### 3. 记录数据

记录物体位置和头部角度，用于后续分析：

```python
data = {
    'timestamp': time.time(),
    'obj_x': obj_x,
    'obj_y': obj_y,
    'yaw': yaw,
    'pitch': pitch
}
```

---

## 与其他 Demo 的区别

| Demo | 运行平台 | 主要功能 |
|------|----------|----------|
| [Demo 13](../13_head_look_around/) | Reachy Mini | 头部运动控制 |
| **Demo 14** | Reachy Mini | 视觉追踪 + 头部控制 |

---

## 相关文档

- [OpenCV 官方文档](https://docs.opencv.org/)
- [OpenCV 颜色检测教程](https://docs.opencv.org/4.x/df/d9d/tutorial_py_colorspaces.html)
- [Reachy Mini SDK 官方文档](https://github.com/pollen-robotics/reachy-minisdk)
- [API 参考文档](../../docs/API_REFERENCE_CN.md)

---

## 许可证

MIT License
