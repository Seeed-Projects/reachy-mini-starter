# YOLO 物体追踪 - 头部 Yaw 版本

使用 Reachy Mini 的头部 Yaw 进行水平方向的 YOLO 物体追踪。

## 文件结构

```
object_tracking_yolo/
├── yolo_detector.py         # YOLO 检测模块
├── position_filter.py       # 位置滤波器
├── head_yaw_controller.py   # 头部 Yaw 控制器
├── track_object.py          # 主程序
└── README.md                # 说明文档
```

## 功能特性

- **YOLO 目标检测**: 支持检测任何 YOLO 类别物体
- **位置滤波器**: 平滑检测坐标波动
- **PID 控制器**: 计算头部 Yaw 调整量
- **头部 Yaw 控制**: 使用头部旋转进行水平追踪（不使用身体 Yaw）

## 使用方法

```bash
# 默认参数追踪瓶子
python track_object.py --class bottle

# 追踪杯子
python track_object.py --class cup

# 追踪人
python track_object.py --class person

# 调整 PID 参数
python track_object.py --class bottle --pid-p 1.5 --pid-d 0.2

# 调整置信度阈值
python track_object.py --class bottle --conf-threshold 0.7

# 调整滤波器参数
python track_object.py --class bottle --filter-window-size 8 --filter-jump-threshold 20

# 组合参数
python track_object.py --class cup --pid-p 1.2 --filter-window-size 6 --conf-threshold 0.6
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--class` | bottle | 目标类别 (bottle, cup, person, cell phone 等) |
| `--model` | yolov8n.pt | YOLO 模型名称 |
| `--conf-threshold` | 0.5 | 置信度阈值 |
| `--iou-threshold` | 0.45 | IOU 阈值 |
| `--pid-p` | 1.0 | PID 比例系数 |
| `--pid-i` | 0.0 | PID 积分系数 |
| `--pid-d` | 0.1 | PID 微分系数 |
| `--filter-window-size` | 5 | 滤波器窗口大小 |
| `--filter-jump-threshold` | 30 | 滤波器跳变阈值（像素） |
| `--window-scale` | 0.6 | 窗口缩放比例 |

## 控制逻辑

```
目标在右侧 (offset > 0) → 头部向右转 (增加 Yaw)
目标在左侧  (offset < 0) → 头部向左转 (减小 Yaw)
目标在中央  (|offset| < 死区) → 不调整
```

## 界面说明

- **黄色十字**: 视野中心（目标应该在此位置）
- **绿色圆圈**: 死区范围（目标在此范围内不控制）
- **绿色大点**: 滤波后的目标位置
- **白色小点**: 原始检测位置
- **绿色连线**: 目标到中心的距离
- **绿色矩形**: YOLO 检测框

## 常见问题

**Q: 追踪方向反了？**
A: 修改 `head_yaw_controller.py` 第 91 行，将 `yaw_adjustment = control * 0.3` 改为 `yaw_adjustment = -control * 0.3`

**Q: 追踪不够稳定？**
A: 增大滤波器窗口 `--filter-window-size`，或增大 PID-D `--pid-d`

**Q: 响应太慢？**
A: 增大 PID-P `--pid-p`，减小滤波器窗口

**Q: 检测不到目标？**
A: 调整 `--conf-threshold` 降低置信度阈值，或检查目标类别名称

**Q: 如何查看支持的目标类别？**
A: 运行程序后会自动显示支持的所有类别
