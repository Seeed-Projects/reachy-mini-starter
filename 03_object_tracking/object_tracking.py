"""
Reachy Mini Object Tracking Demo (Demo 3)

使用 YOLO 进行目标检测，并控制 Reachy Mini 追踪目标物体，
使目标物体始终保持在视野中央。

功能：
1. 利用 demo1 的方式获取视频流
2. 使用 YOLO v8 进行实时目标检测
3. 利用 demo2 的方式控制机器人追踪目标

前置条件：
    pip install reachy-mini opencv-python ultralytics

使用：
    python object_tracking.py --class person --backend default
    python object_tracking.py --class cup --conf-threshold 0.5
"""

import argparse
import time
import math
from collections import deque

import cv2
import numpy as np

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Install with: pip install ultralytics")

from reachy_mini import ReachyMini


class ObjectTracker:
    """物体追踪控制器"""

    def __init__(self, reachy_mini, model_name='yolov8n.pt', target_class='person',
                 conf_threshold=0.5, iou_threshold=0.45, max_history=5,
                 pid_p=0.8, pid_i=0.0, pid_d=0.2):
        """
        初始化物体追踪器

        Args:
            reachy_mini: ReachyMini 实例
            model_name: YOLO 模型名称 (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt)
            target_class: 目标类别名称 (person, cup, bottle, cell phone 等)
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值
            max_history: 历史轨迹最大长度
            pid_p: PID 控制器比例系数
            pid_i: PID 控制器积分系数
            pid_d: PID 控制器微分系数
        """
        self.mini = reachy_mini
        self.target_class = target_class
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.max_history = max_history

        # 加载 YOLO 模型
        if YOLO_AVAILABLE:
            self.model = YOLO(model_name)
            # 获取所有类别名称
            self.class_names = self.model.names
            print(f"YOLO 模型加载成功: {model_name}")
            print(f"可用类别: {', '.join(self.class_names.values())}")

            # 检查目标类别是否有效
            if target_class not in self.class_names.values():
                print(f"Warning: 目标类别 '{target_class}' 不在支持的类别中")
                print(f"将尝试检测所有类别...")
        else:
            self.model = None
            self.class_names = {}
            print("Error: YOLO 不可用，请安装 ultralytics")

        # PID 控制器参数
        self.pid_p = pid_p
        self.pid_i = pid_i
        self.pid_d = pid_d

        # 历史轨迹 (用于平滑和预测)
        self.center_history = deque(maxlen=max_history)
        self.size_history = deque(maxlen=max_history)

        # 积分累积和上一次误差
        self.integral_x = 0
        self.integral_y = 0
        self.last_error_x = 0
        self.last_error_y = 0

        # 追踪状态
        self.is_tracking = False
        self.last_detection_time = 0
        self.detection_timeout = 1.0  # 如果超过1秒没有检测到目标，停止追踪

        # 控制参数
        self.control_speed = 0.3  # 控制响应速度 (秒)
        self.dead_zone = 0.05  # 死区比例（目标在中央5%范围内时不调整）

    def get_frame_center(self, frame):
        """获取帧中心点坐标"""
        height, width = frame.shape[:2]
        return width // 2, height // 2

    def normalize_to_center(self, x, y, frame_width, frame_height):
        """
        将图像坐标归一化到中心坐标系

        Args:
            x, y: 图像坐标
            frame_width, frame_height: 帧尺寸

        Returns:
            (norm_x, norm_y): 归一化坐标，范围 [-1, 1]，(0, 0) 表示中心
        """
        center_x = frame_width / 2
        center_y = frame_height / 2
        norm_x = (x - center_x) / center_x
        norm_y = (y - center_y) / center_y
        return norm_x, norm_y

    def pid_control(self, error_x, error_y, dt):
        """
        PID 控制器计算控制量

        Args:
            error_x, error_y: 当前误差（归一化坐标）
            dt: 时间步长

        Returns:
            (control_x, control_y): 控制量
        """
        # 比例项
        p_x = self.pid_p * error_x
        p_y = self.pid_p * error_y

        # 积分项
        self.integral_x += error_x * dt
        self.integral_y += error_y * dt
        # 限制积分累积
        self.integral_x = max(-1.0, min(1.0, self.integral_x))
        self.integral_y = max(-1.0, min(1.0, self.integral_y))
        i_x = self.pid_i * self.integral_x
        i_y = self.pid_i * self.integral_y

        # 微分项
        d_x = self.pid_d * (error_x - self.last_error_x) / dt if dt > 0 else 0
        d_y = self.pid_d * (error_y - self.last_error_y) / dt if dt > 0 else 0

        # 更新上次误差
        self.last_error_x = error_x
        self.last_error_y = error_y

        return p_x + i_x + d_x, p_y + i_y + d_y

    def detect_objects(self, frame):
        """
        使用 YOLO 检测物体

        Args:
            frame: 输入图像

        Returns:
            detections: 检测结果列表 [(x1, y1, x2, y2, conf, class_id), ...]
        """
        if self.model is None:
            return []

        results = self.model(frame, conf=self.conf_threshold, iou=self.iou_threshold, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    detections.append((x1, y1, x2, y2, conf, class_id))

        return detections

    def filter_target_class(self, detections):
        """
        过滤出目标类别的检测

        Args:
            detections: 所有检测结果

        Returns:
            target_detections: 目标类别的检测结果
        """
        if not detections:
            return []

        # 获取目标类别ID
        target_id = None
        for class_id, class_name in self.class_names.items():
            if class_name == self.target_class:
                target_id = class_id
                break

        if target_id is None:
            # 如果目标类别不存在，返回所有检测
            return detections

        return [d for d in detections if d[5] == target_id]

    def select_best_target(self, detections, frame_width, frame_height):
        """
        从检测结果中选择最佳追踪目标

        策略：选择最接近中心的检测框

        Args:
            detections: 检测结果
            frame_width, frame_height: 帧尺寸

        Returns:
            best_detection: 最佳检测结果或 None
        """
        if not detections:
            return None

        center_x = frame_width / 2
        center_y = frame_height / 2

        best_detection = None
        min_distance = float('inf')

        for det in detections:
            x1, y1, x2, y2, conf, class_id = det
            # 计算检测框中心
            det_center_x = (x1 + x2) / 2
            det_center_y = (y1 + y2) / 2

            # 计算到图像中心的距离
            distance = math.sqrt((det_center_x - center_x) ** 2 + (det_center_y - center_y) ** 2)

            if distance < min_distance:
                min_distance = distance
                best_detection = det

        return best_detection

    def update_control(self, detection, frame_width, frame_height, dt):
        """
        根据检测结果更新控制

        Args:
            detection: 检测结果 (x1, y1, x2, y2, conf, class_id)
            frame_width, frame_height: 帧尺寸
            dt: 时间步长
        """
        x1, y1, x2, y2, conf, class_id = detection

        # 计算检测框中心
        det_center_x = (x1 + x2) / 2
        det_center_y = (y1 + y2) / 2

        # 归一化到中心坐标系
        error_x, error_y = self.normalize_to_center(det_center_x, det_center_y, frame_width, frame_height)

        # 检查是否在死区内
        if abs(error_x) < self.dead_zone and abs(error_y) < self.dead_zone:
            return  # 在死区内，不调整

        # PID 控制计算
        control_x, control_y = self.pid_control(error_x, error_y, dt)

        # 限制控制量范围
        control_x = max(-1.0, min(1.0, control_x))
        control_y = max(-1.0, min(1.0, control_y))

        # 转换为图像坐标偏移（用于 look_at_image）
        # 注意：control_x 是左右偏移，control_y 是上下偏移
        # look_at_image 使用像素坐标
        offset_x = int(control_x * frame_width * 0.1)  # 缩放因子，避免移动过大
        offset_y = int(control_y * frame_height * 0.1)

        target_x = int(frame_width / 2 + offset_x)
        target_y = int(frame_height / 2 + offset_y)

        # 执行头部运动
        try:
            self.mini.look_at_image(target_x, target_y, duration=self.control_speed)
        except Exception as e:
            print(f"Error controlling robot: {e}")

    def draw_detections(self, frame, detections, target_detection=None):
        """
        在图像上绘制检测结果

        Args:
            frame: 输入图像
            detections: 所有检测结果
            target_detection: 当前追踪的目标
        """
        for det in detections:
            x1, y1, x2, y2, conf, class_id = det
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # 确定颜色
            if det == target_detection:
                color = (0, 255, 0)  # 绿色表示追踪目标
                line_thickness = 3
            else:
                color = (0, 0, 255)  # 红色表示其他检测
                line_thickness = 2

            # 绘制边界框
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, line_thickness)

            # 获取类别名称
            class_name = self.class_names.get(class_id, f"Class_{class_id}")

            # 绘制标签
            label = f"{class_name}: {conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return frame

    def track(self, frame):
        """
        处理一帧图像进行追踪

        Args:
            frame: 输入图像

        Returns:
            annotated_frame: 绘制了检测结果的图像
        """
        height, width = frame.shape[:2]
        current_time = time.time()
        dt = current_time - self.last_detection_time if self.last_detection_time > 0 else 0.03

        # 检测所有物体
        detections = self.detect_objects(frame)

        # 过滤目标类别
        target_detections = self.filter_target_class(detections)

        # 选择最佳追踪目标
        target_detection = self.select_best_target(target_detections, width, height)

        # 更新追踪状态
        if target_detection is not None:
            self.is_tracking = True
            self.last_detection_time = current_time

            # 更新控制
            self.update_control(target_detection, width, height, dt)
        else:
            # 检查是否超时
            if current_time - self.last_detection_time > self.detection_timeout:
                self.is_tracking = False
                # 重置 PID 状态
                self.integral_x = 0
                self.integral_y = 0
                self.last_error_x = 0
                self.last_error_y = 0

        # 绘制检测结果
        annotated_frame = self.draw_detections(frame, detections, target_detection)

        # 绘制追踪状态
        status_text = f"Tracking: {'YES' if self.is_tracking else 'NO'}"
        status_color = (0, 255, 0) if self.is_tracking else (0, 0, 255)
        cv2.putText(annotated_frame, status_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

        # 绘制目标类别
        class_text = f"Target: {self.target_class}"
        cv2.putText(annotated_frame, class_text, (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 绘制中心十字
        center_x, center_y = width // 2, height // 2
        cv2.drawMarker(annotated_frame, (center_x, center_y), (0, 255, 255),
                      cv2.MARKER_CROSS, 20, 2)

        return annotated_frame


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reachy Mini Object Tracking with YOLO"
    )
    parser.add_argument(
        '--backend',
        type=str,
        choices=['default', 'gstreamer', 'webrtc'],
        default='default',
        help='Media backend to use'
    )
    parser.add_argument(
        '--resolution',
        type=str,
        default='640x480',
        help='Camera resolution (640x480, 800x600, 1280x720)'
    )
    parser.add_argument(
        '--window-scale',
        type=float,
        default=0.6,
        help='Window display scale (0.1 - 1.0)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='yolov8n.pt',
        help='YOLO model name (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt)'
    )
    parser.add_argument(
        '--class',
        type=str,
        default='person',
        dest='target_class',
        help='Target object class to track'
    )
    parser.add_argument(
        '--conf-threshold',
        type=float,
        default=0.5,
        help='Confidence threshold for detection'
    )
    parser.add_argument(
        '--iou-threshold',
        type=float,
        default=0.45,
        help='IOU threshold for NMS'
    )
    parser.add_argument(
        '--pid-p',
        type=float,
        default=0.8,
        help='PID proportional gain'
    )
    parser.add_argument(
        '--pid-i',
        type=float,
        default=0.0,
        help='PID integral gain'
    )
    parser.add_argument(
        '--pid-d',
        type=float,
        default=0.2,
        help='PID derivative gain'
    )
    parser.add_argument(
        '--control-speed',
        type=float,
        default=0.3,
        help='Control response speed (seconds)'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Reachy Mini Object Tracking Demo")
    print("=" * 60)
    print(f"Target class: {args.target_class}")
    print(f"YOLO model: {args.model}")
    print(f"Confidence threshold: {args.conf_threshold}")
    print(f"PID gains: P={args.pid_p}, I={args.pid_i}, D={args.pid_d}")
    print("=" * 60)
    print("\nStarting tracking...")
    print("Press 'q' to quit\n")

    # 解析分辨率
    try:
        width, height = map(int, args.resolution.split('x'))
    except ValueError:
        print(f"Invalid resolution format: {args.resolution}")
        print("Using default resolution: 640x480")
        width, height = 640, 480

    # 窗口缩放比例限制
    window_scale = max(0.1, min(1.0, args.window_scale))

    with ReachyMini(media_backend=args.backend) as reachy_mini:
        # 设置摄像头分辨率
        try:
            reachy_mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            reachy_mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            print(f"Camera resolution set to: {width}x{height}")
        except Exception as e:
            print(f"Warning: Could not set camera resolution: {e}")

        # 初始化追踪器
        tracker = ObjectTracker(
            reachy_mini=reachy_mini,
            model_name=args.model,
            target_class=args.target_class,
            conf_threshold=args.conf_threshold,
            iou_threshold=args.iou_threshold,
            pid_p=args.pid_p,
            pid_i=args.pid_i,
            pid_d=args.pid_d,
        )
        tracker.control_speed = args.control_speed

        # 计算显示窗口大小
        display_width = int(width * window_scale)
        display_height = int(height * window_scale)
        print(f"Display window size: {display_width}x{display_height}")

        try:
            while True:
                # 获取摄像头画面 (demo1 方式)
                frame = reachy_mini.media.get_frame()

                if frame is None:
                    print("Failed to grab frame.")
                    continue

                # 执行追踪
                annotated_frame = tracker.track(frame)

                # 缩放显示窗口
                if window_scale != 1.0:
                    display_frame = cv2.resize(annotated_frame, (display_width, display_height))
                else:
                    display_frame = annotated_frame

                # 显示结果
                cv2.imshow("Reachy Mini Object Tracking", display_frame)

                # 按 'q' 退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nExiting...")
                    break

        except KeyboardInterrupt:
            print("\nInterrupted. Closing viewer...")
        finally:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
