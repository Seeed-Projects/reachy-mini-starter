# YOLO Object Tracking Web Application

基于 Web 的 YOLO 物体追踪系统，为 Reachy Mini 提供现代化的网页控制界面。

## 功能特性

### 核心功能
- **YOLO 目标检测**: 支持检测任何 YOLO 类别物体
- **双轴追踪**: 同时使用头部 Pitch 和 Yaw 进行追踪
- **实时视频流**: 通过 MJPEG 流式传输摄像头画面
- **参数实时调节**: 动态调整 PID 参数、检测器参数、滤波器参数
- **现代化界面**: 响应式设计的 Web 控制面板

### 控制功能
- **启动/停止追踪**: 一键控制追踪状态
- **目标类别选择**: 下拉菜单选择检测目标
- **置信度调节**: 滑块实时调整检测阈值
- **PID 参数调节**: 独立调节 Pitch 和 Yaw 轴的 PID 参数
- **滤波器设置**: 调整位置滤波器的窗口大小和跳变阈值

## 项目结构

```
object_tracking_yolo_web/
├── main.py                          # 主入口文件
├── requirements.txt                 # Python 依赖
├── README.md                        # 说明文档
├── backend/                         # 后端代码
│   ├── __init__.py
│   ├── api.py                       # FastAPI 路由定义
│   ├── tracking_manager.py          # 追踪管理器
│   ├── yolo_wrapper.py              # YOLO 检测器封装
│   └── tracker_core.py              # 核心追踪逻辑
└── frontend/                        # 前端代码
    ├── __init__.py
    ├── static/                      # 静态资源
    │   ├── css/
    │   │   └── style.css            # 样式表
    │   └── js/
    │       └── app.js               # 前端 JavaScript
    └── templates/                   # HTML 模板
        └── index.html               # 主页面
```

## 安装依赖

```bash
# 进入项目目录
cd 03_object_tracking/object_tracking_yolo_web

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 1. 启动 Web 服务器

```bash
python main.py
```

服务器启动后，访问以下地址：

- **Web 界面**: http://localhost:8123
- **API 文档**: http://localhost:8123/docs
- **视频流**: http://localhost:8123/video

### 2. Web 界面操作

1. **启动追踪**
   - 点击 "Start Tracking" 按钮开始追踪
   - 视频流会显示检测到的物体和追踪状态

2. **选择目标类别**
   - 在 "Detector Settings" 中选择目标类别
   - 支持的类别：bottle, cup, person, cell phone 等

3. **调整检测参数**
   - 调整置信度阈值（Confidence Threshold）
   - 较低的阈值会检测更多物体，但可能增加误检

4. **调整 PID 参数**
   - 使用 "Axis Tabs" 切换 Pitch 或 Yaw 轴
   - 调整 P（比例）、I（积分）、D（微分）参数
   - 调整 Speed（增益）参数

5. **调整滤波器参数**
   - Window Size: 移动平均窗口大小
   - Jump Threshold: 跳变抑制阈值（像素）

## API 端点

### 控制端点

- `POST /api/control/start` - 启动追踪
- `POST /api/control/stop` - 停止追踪
- `POST /api/control/reset` - 重置追踪状态

### 参数端点

- `GET /api/params` - 获取当前参数
- `POST /api/params/pitch` - 更新 Pitch 参数
- `POST /api/params/yaw` - 更新 Yaw 参数
- `POST /api/params/detector` - 更新检测器设置
- `POST /api/params/filter` - 更新滤波器设置

### 信息端点

- `GET /api/info` - 获取当前追踪信息
- `GET /api/classes` - 获取可用的 YOLO 类别
- `GET /api/video` - 视频流（MJPEG）

## 参数说明

### PID 参数

- **P (Proportional)**: 比例系数，控制响应速度
  - 范围: 0.0 - 4.0
  - 默认: 0.5
  - 较高值：响应更快，但可能不稳定
  - 较低值：响应更慢，但更稳定

- **I (Integral)**: 积分系数，消除稳态误差
  - 范围: 0.0 - 1.0
  - 默认: 0.0
  - 大多数情况下设为 0

- **D (Derivative)**: 微分系数，减少超调
  - 范围: 0.0 - 1.0
  - 默认: 0.0
  - 可以减少震荡，但可能放大噪声

- **Speed (Gain)**: 速度增益，控制调整幅度
  - 范围: 0.01 - 0.5
  - 默认: 0.08
  - 较高值：移动更快，但可能不稳定

### 检测器参数

- **Confidence Threshold**: 置信度阈值
  - 范围: 0.1 - 1.0
  - 默认: 0.3
  - 较低值：检测更多物体
  - 较高值：只检测高置信度物体

### 滤波器参数

- **Window Size**: 滑动窗口大小
  - 范围: 1 - 20
  - 默认: 5
  - 较大值：更平滑，但响应更慢

- **Jump Threshold**: 跳变阈值
  - 范围: 10 - 100 像素
  - 默认: 30
  - 抑制检测位置的突然跳变

## 技术架构

### 后端
- **FastAPI**: 现代化的 Python Web 框架
- **Ultralytics YOLO**: 目标检测
- **OpenCV**: 图像处理和视频编码
- **Threading**: 后台追踪线程

### 前端
- **HTML5/CSS3**: 现代化响应式界面
- **JavaScript (ES6+)**: 原生 JS，无框架依赖
- **Fetch API**: 与后端通信
- **MJPEG Streaming**: 实时视频流

## 与原版对比

### 原版 (OpenCV GUI)
- 使用 OpenCV 的 `createTrackbar` 创建控制界面
- 需要远程桌面或直接操作
- 界面较为简陋

### Web 版本
- 现代化的 Web 界面
- 可以在任何设备的浏览器中访问
- 更好的用户体验
- RESTful API，易于集成

## 常见问题

**Q: 视频流卡顿？**
A: 检查网络带宽，可以降低帧率或分辨率。

**Q: 追踪不够稳定？**
A: 增大滤波器窗口，或调整 PID 参数。

**Q: 检测不到目标？**
A: 降低置信度阈值，或检查目标类别名称。

**Q: 响应太慢？**
A: 增大 P 参数，或减小滤波器窗口。

**Q: 如何修改端口？**
A: 修改 `main.py` 中的 `port=8123`。

## 开发说明

### 添加新的 API 端点

在 `backend/api.py` 中添加新的路由：

```python
@app.post("/your-endpoint")
async def your_function():
    # Your code here
    return {"success": True}
```

### 修改前端界面

- **样式**: 编辑 `frontend/static/css/style.css`
- **逻辑**: 编辑 `frontend/static/js/app.js`
- **布局**: 编辑 `frontend/templates/index.html`

## 许可证

本项目基于 Reachy Mini Lite 示例代码开发。
