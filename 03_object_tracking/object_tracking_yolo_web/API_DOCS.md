# YOLO 目标追踪系统 - API 接口文档

## 基础信息

- **Base URL**: `http://localhost:8123`
- **API 前缀**: `/api`
- **视频流**: `/video` (MJPEG 流)

---

## 接口列表

### 1. 健康检查

**接口**: `GET /api/health`

**说明**: 检查后端是否初始化完成

**响应示例**:
```json
{
  "status": "ready",           // "ready" 或 "initializing"
  "message": "Tracking manager is ready"
}
```

---

### 2. 获取追踪信息

**接口**: `GET /api/info`

**说明**: 获取当前追踪状态和实时数据

**响应示例**:
```json
{
  "is_running": true,          // 追踪是否运行中
  "is_tracking": true,         // 是否检测到目标
  "target_center": [640, 360], // 目标中心坐标 [x, y]
  "filtered_center": [638, 362], // 滤波后中心坐标
  "pitch": 0.15,               // 当前俯仰角 (弧度)
  "yaw": -0.08,                // 当前偏航角 (弧度)
  "target_class": "bottle",    // 目标类别
  "detection_count": 2         // 检测到的目标数量
}
```

**字段说明**:
- `is_running`: 追踪系统是否正在运行
- `is_tracking`: 是否成功检测并追踪到目标
- `target_center`: 原始检测框的中心点坐标
- `filtered_center`: 经过滤波处理后的中心点坐标
- `pitch`: 头部俯仰角，单位弧度，正值向上，负值向下
- `yaw`: 头部偏航角，单位弧度，正值向右，负值向左
- `target_class`: 当前追踪的目标类别名称
- `detection_count`: 当前帧检测到的目标数量

---

### 3. 获取可用类别

**接口**: `GET /api/classes`

**说明**: 获取 YOLO 模型支持的所有目标类别

**响应示例**:
```json
{
  "classes": [
    "person", "bicycle", "car", "motorcycle", "airplane",
    "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat",
    "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon",
    "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
    "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator",
    "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush"
  ]
}
```

---

### 4. 获取当前参数

**接口**: `GET /api/params`

**说明**: 获取所有控制器的当前参数

**响应示例**:
```json
{
  "pitch": {
    "p": 0.5,       // 比例系数 (Proportional)
    "i": 0.0,       // 积分系数 (Integral)
    "d": 0.0,       // 微分系数 (Derivative)
    "gain": 0.08    // 速度增益
  },
  "yaw": {
    "p": 0.5,
    "i": 0.0,
    "d": 0.0,
    "gain": 0.08
  },
  "detector": {
    "target_class": "bottle",    // 目标类别
    "conf_threshold": 0.3        // 置信度阈值
  },
  "filter": {
    "window_size": 5,            // 滤波窗口大小
    "jump_threshold": 30         // 跳变阈值(像素)
  }
}
```

**参数说明**:

#### Pitch (俯仰) 参数
- `p`: 比例系数，控制响应速度，范围 0-4.0
- `i`: 积分系数，消除稳态误差，范围 0-1.0
- `d`: 微分系数，减少超调，范围 0-1.0
- `gain`: 速度增益，控制角度变化速度，范围 0.01-0.5

#### Yaw (偏航) 参数
- `p`: 比例系数，控制响应速度，范围 0-4.0
- `i`: 积分系数，消除稳态误差，范围 0-1.0
- `d`: 微分系数，减少超调，范围 0-1.0
- `gain`: 速度增益，控制角度变化速度，范围 0.01-0.5

#### Detector (检测器) 参数
- `target_class`: 要追踪的目标类别名称
- `conf_threshold`: 检测置信度阈值，范围 0.1-1.0

#### Filter (滤波器) 参数
- `window_size`: 移动平均窗口大小，范围 1-20
- `jump_threshold`: 跳变抑制阈值(像素)，范围 10-100

---

### 5. 更新 Pitch 参数

**接口**: `POST /api/params/pitch`

**说明**: 更新俯仰轴的 PID 控制参数

**请求体** (所有字段可选):
```json
{
  "p": 0.5,       // 比例系数，范围: 0-4.0
  "i": 0.0,       // 积分系数，范围: 0-1.0
  "d": 0.0,       // 微分系数，范围: 0-1.0
  "gain": 0.08    // 速度增益，范围: 0.01-0.5
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "Pitch parameters updated"
}
```

**调优建议**:
- 增大 `p`: 响应更快，但可能震荡
- 增大 `i`: 减小稳态误差，但可能增加超调
- 增大 `d`: 减少超调和震荡，但可能对噪声敏感
- 增大 `gain`: 角度变化更快，但可能不稳定

---

### 6. 更新 Yaw 参数

**接口**: `POST /api/params/yaw`

**说明**: 更新偏航轴的 PID 控制参数

**请求体** (所有字段可选):
```json
{
  "p": 0.5,       // 比例系数，范围: 0-4.0
  "i": 0.0,       // 积分系数，范围: 0-1.0
  "d": 0.0,       // 微分系数，范围: 0-1.0
  "gain": 0.08    // 速度增益，范围: 0.01-0.5
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "Yaw parameters updated"
}
```

---

### 7. 更新检测器设置

**接口**: `POST /api/params/detector`

**说明**: 更新目标检测器的设置

**请求体** (所有字段可选):
```json
{
  "target_class": "bottle",    // 目标类别
  "conf_threshold": 0.3        // 置信度阈值，范围: 0.1-1.0
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "Detector settings updated"
}
```

**参数说明**:
- `target_class`: 从 /api/classes 获取的有效类别名
- `conf_threshold`: 置信度阈值，越高检测越严格但可能漏检

---

### 8. 更新滤波器设置

**接口**: `POST /api/params/filter`

**说明**: 更新位置滤波器的参数

**请求体** (所有字段可选):
```json
{
  "window_size": 5,      // 滤波窗口大小，范围: 1-20
  "jump_threshold": 30   // 跳变阈值(像素)，范围: 10-100
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "Filter settings updated"
}
```

**参数说明**:
- `window_size`: 移动平均窗口大小，越大越平滑但延迟越高
- `jump_threshold`: 跳变抑制阈值，过滤大的位置跳变

---

### 9. 控制接口

#### 9.1 开始追踪

**接口**: `POST /api/control/start`

**说明**: 启动目标追踪

**响应示例**:
```json
{
  "success": true,
  "message": "Tracking started"
}
```

#### 9.2 停止追踪

**接口**: `POST /api/control/stop`

**说明**: 停止目标追踪

**响应示例**:
```json
{
  "success": true,
  "message": "Tracking stopped"
}
```

#### 9.3 重置追踪

**接口**: `POST /api/control/reset`

**说明**: 重置追踪状态（PID 积分、滤波器等）

**响应示例**:
```json
{
  "success": true,
  "message": "Tracking reset"
}
```

---

## 前端调用示例

### JavaScript 示例

```javascript
// 获取当前参数
async function getParams() {
    const response = await fetch('http://localhost:8123/api/params');
    const data = await response.json();
    console.log('Pitch P:', data.pitch.p);
    console.log('Yaw gain:', data.yaw.gain);
}

// 更新 Pitch 参数
async function updatePitchParams() {
    const response = await fetch('http://localhost:8123/api/params/pitch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            p: 0.6,
            i: 0.01,
            d: 0.05,
            gain: 0.1
        })
    });
    const data = await response.json();
    console.log(data.message);
}

// 更新检测器设置
async function updateDetector() {
    const response = await fetch('http://localhost:8123/api/params/detector', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            target_class: 'cup',
            conf_threshold: 0.5
        })
    });
    const data = await response.json();
    console.log(data.message);
}

// 启动追踪
async function startTracking() {
    const response = await fetch('http://localhost:8123/api/control/start', {
        method: 'POST'
    });
    const data = await response.json();
    console.log(data.message);
}
```

---

## Python 示例

```python
import requests

BASE_URL = 'http://localhost:8123'

# 获取当前参数
def get_params():
    response = requests.get(f'{BASE_URL}/api/params')
    return response.json()

# 更新 Pitch 参数
def update_pitch_params():
    response = requests.post(
        f'{BASE_URL}/api/params/pitch',
        json={'p': 0.6, 'i': 0.01, 'd': 0.05, 'gain': 0.1}
    )
    return response.json()

# 更新检测器设置
def update_detector():
    response = requests.post(
        f'{BASE_URL}/api/params/detector',
        json={'target_class': 'cup', 'conf_threshold': 0.5}
    )
    return response.json()

# 启动追踪
def start_tracking():
    response = requests.post(f'{BASE_URL}/api/control/start')
    return response.json()
```

---

## 错误处理

所有接口在发生错误时会返回相应的 HTTP 状态码：

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `500 Internal Server Error`: 服务器内部错误

建议前端实现适当的错误处理和用户提示。

---

## 调试技巧

1. 使用浏览器开发者工具的 Network 面板查看 API 调用
2. 访问 `http://localhost:8123/docs` 查看自动生成的 API 文档（Swagger UI）
3. 检查浏览器控制台是否有 JavaScript 错误
4. 使用 curl 测试接口：
   ```bash
   curl http://localhost:8123/api/health
   curl http://localhost:8123/api/params
   ```
