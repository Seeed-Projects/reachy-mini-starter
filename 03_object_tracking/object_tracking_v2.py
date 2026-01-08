"""
Reachy Mini Object Tracking Demo V2 (Demo 3)

使用 YOLO 进行目标检测，并控制 Reachy Mini 追踪目标物体，
使目标物体始终保持在视野中央。

V2 版本改进：
- 同时控制 Yaw（水平）和 Pitch（垂直）方向
- 简化控制逻辑，直接使用检测框中心坐标
- 添加平滑控制以减少抖动
- 添加俯仰角限制以保护硬件

功能：
1. 利用 demo1 的方式获取视频流
2. 使用 YOLO v8 进行实时目标检测
3. 利用 demo2 的方式控制机器人追踪目标（水平和垂直）

前置条件：
    pip install reachy-mini opencv-python ultralytics

使用：
    python object_tracking_v2.py --class bottle
    python object_tracking_v2.py --class cup --conf-threshold 0.5 --smooth-factor 0.3
"""

import argparse
import time
import math
from collections import deque

import cv2
import numpy as np

# OpenCV 的卡尔曼滤波器
KalmanFilter = cv2.KalmanFilter


class KalmanTracker:
    """
    使用卡尔曼滤波器平滑目标位置跟踪

    卡尔曼滤波器可以：
    1. 预测目标下一时刻的位置
    2. 平滑测量噪声（YOLO 检测的抖动）
    3. 提供更稳定的轨迹估计
    """

    def __init__(self, process_noise_scale=0.001, measurement_noise_scale=0.1):
        """
        初始化卡尔曼滤波器

        Args:
            process_noise_scale: 过程噪声协方差（越小越信任模型预测）
            measurement_noise_scale: 测量噪声协方差（越小越信任测量值）
        """
        # 状态向量 [x, y, vx, vy] - 位置和速度
        self.kf = cv2.KalmanFilter(4, 2)

        # 测量向量 [x, y]
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                             [0, 1, 0, 0]], np.float32)

        # 状态转移矩阵（匀速运动模型）
        self.kf.transitionMatrix = np.array([[1, 0, 1, 0],
                                            [0, 1, 0, 1],
                                            [0, 0, 1, 0],
                                            [0, 0, 0, 1]], np.float32)

        # 过程噪声协方差
        self.kf.processNoiseCov = process_noise_scale * np.eye(4, dtype=np.float32)

        # 测量噪声协方差
        self.kf.measurementNoiseCov = measurement_noise_scale * np.eye(2, dtype=np.float32)

        # 初始化状态
        self.kf.statePre = np.zeros((4, 1), dtype=np.float32)
        self.kf.statePost = np.zeros((4, 1), dtype=np.float32)

        self.initialized = False

    def update(self, measurement_x, measurement_y):
        """
        更新滤波器并返回平滑后的位置

        Args:
            measurement_x, measurement_y: 测量值（YOLO 检测结果）

        Returns:
            (smooth_x, smooth_y): 平滑后的位置
        """
        if not self.initialized:
            # 第一次测量，直接初始化
            self.kf.statePost[0, 0] = measurement_x
            self.kf.statePost[1, 0] = measurement_y
            self.kf.statePost[2, 0] = 0  # 初始速度为 0
            self.kf.statePost[3, 0] = 0
            self.initialized = True
            return measurement_x, measurement_y

        # 预测步骤
        prediction = self.kf.predict()

        # 更新步骤（加入测量值）
        measurement = np.array([[measurement_x], [measurement_y]], np.float32)
        estimated = self.kf.correct(measurement)

        # 返回估计的位置
        smooth_x = estimated[0, 0]
        smooth_y = estimated[1, 0]

        return smooth_x, smooth_y

    def predict(self):
        """
        仅预测步骤（用于丢失目标时的外推）

        Returns:
            (pred_x, pred_y): 预测的位置
        """
        if not self.initialized:
            return None, None

        prediction = self.kf.predict()
        return prediction[0, 0], prediction[1, 0]

    def reset(self):
        """重置滤波器"""
        self.initialized = False
        self.kf.statePre = np.zeros((4, 1), dtype=np.float32)
        self.kf.statePost = np.zeros((4, 1), dtype=np.float32)

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Install with: pip install ultralytics")

from reachy_mini import ReachyMini


class ObjectTrackerV2:
    """物体追踪控制器 V2 - 支持水平和垂直追踪，带卡尔曼滤波"""

    # 头部俯仰角限制（度）- 保护硬件
    MAX_PITCH_UP = -30      # 向上看（负角度）
    MAX_PITCH_DOWN = 35     # 向下看（正角度）

    def __init__(self, reachy_mini, model_name='yolov8n.pt', target_class='person',
                 conf_threshold=0.5, iou_threshold=0.45, max_history=5,
                 smooth_factor=0.3, dead_zone=0.05, detection_timeout=1.0,
                 use_kalman=True, kalman_process_noise=0.001, kalman_measurement_noise=0.1):
        """
        初始化物体追踪器 V2

        Args:
            reachy_mini: ReachyMini 实例
            model_name: YOLO 模型名称 (yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt)
            target_class: 目标类别名称 (person, cup, bottle, cell phone 等)
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值
            max_history: 历史轨迹最大长度
            smooth_factor: 平滑因子 (0-1)，越小越平滑
            dead_zone: 死区比例，目标在中央此范围内时不调整
            detection_timeout: 检测超时时间（秒）
            use_kalman: 是否使用卡尔曼滤波
            kalman_process_noise: 卡尔曼过程噪声（越小越平滑）
            kalman_measurement_noise: 卡尔曼测量噪声（越小越信任测量）
        """
        self.mini = reachy_mini
        self.target_class = target_class
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.max_history = max_history
        self.smooth_factor = smooth_factor
        self.dead_zone = dead_zone
        self.detection_timeout = detection_timeout
        self.use_kalman = use_kalman

        # 加载 YOLO 模型
        if YOLO_AVAILABLE:
            self.model = YOLO(model_name)
            self.class_names = self.model.names
            print(f"YOLO 模型加载成功: {model_name}")
            print(f"可用类别: {', '.join(self.class_names.values())}")

            if target_class not in self.class_names.values():
                print(f"Warning: 目标类别 '{target_class}' 不在支持的类别中")
        else:
            self.model = None
            self.class_names = {}

        # 平滑控制：使用指数移动平均
        self.smooth_x = None
        self.smooth_y = None

        # 历史轨迹
        self.center_history = deque(maxlen=max_history)

        # 追踪状态
        self.is_tracking = False
        self.last_detection_time = 0
        self.lost_track_count = 0

        # 控制参数
        self.control_speed = 0.15  # 控制响应速度（秒）

        # 运动范围限制（像素距离中心的百分比）
        self.max_horizontal_offset = 0.45  # 最大水平偏移 45%
        self.max_vertical_offset = 0.40    # 最大垂直偏移 40%

        # 运动插值
        self.last_target_x = None
        self.last_target_y = None
        self.last_command_time = None

        # 卡尔曼滤波器
        if self.use_kalman:
            self.kalman_tracker = KalmanTracker(
                process_noise_scale=kalman_process_noise,
                measurement_noise_scale=kalman_measurement_noise
            )
        else:
            self.kalman_tracker = None

    def get_frame_center(self, frame):
        """获取帧中心点坐标"""
        height, width = frame.shape[:2]
        return width / 2, height / 2

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

    def apply_smoothing(self, target_x, target_y):
        """
        应用平滑控制（卡尔曼滤波 + EMA）

        Args:
            target_x, target_y: 目标位置

        Returns:
            (smooth_x, smooth_y): 平滑后的位置
        """
        # 先使用卡尔曼滤波
        if self.use_kalman and self.kalman_tracker is not None:
            kalman_x, kalman_y = self.kalman_tracker.update(target_x, target_y)
        else:
            kalman_x, kalman_y = target_x, target_y

        # 再使用 EMA 进行额外平滑
        if self.smooth_x is None:
            self.smooth_x = kalman_x
            self.smooth_y = kalman_y
        else:
            self.smooth_x = self.smooth_factor * kalman_x + (1 - self.smooth_factor) * self.smooth_x
            self.smooth_y = self.smooth_factor * kalman_y + (1 - self.smooth_factor) * self.smooth_y

        return self.smooth_x, self.smooth_y

    def interpolate_motion(self, current_time, frame_width, frame_height):
        """
        运动插值 - 在两次检测之间生成平滑的中间目标点

        Args:
            current_time: 当前时间
            frame_width, frame_height: 帧尺寸

        Returns:
            (interp_x, interp_y) or (None, None): 插值后的目标点
        """
        if self.last_target_x is None or self.last_command_time is None:
            return None, None

        time_since_last = current_time - self.last_command_time

        # 如果时间太短，不进行插值
        if time_since_last < 0.02:
            return None, None

        # 计算插值进度（基于控制速度）
        progress = min(time_since_last / self.control_speed, 1.0)

        # 使用缓动函数让运动更丝滑
        # ease-in-out: 2t^2 for t < 0.5, 1 - (1 - 2(1-t))^2 for t >= 0.5
        if progress < 0.5:
            eased_progress = 2 * progress * progress
        else:
            eased_progress = 1 - 2 * (1 - progress) * (1 - progress)

        # 插值计算：从当前位置向中心移动
        center_x = frame_width / 2
        center_y = frame_height / 2

        interp_x = self.last_target_x + (center_x - self.last_target_x) * eased_progress
        interp_y = self.last_target_y + (center_y - self.last_target_y) * eased_progress

        return interp_x, interp_y

    def clamp_target_position(self, x, y, frame_width, frame_height):
        """
        限制目标位置在安全范围内

        Args:
            x, y: 目标像素坐标
            frame_width, frame_height: 帧尺寸

        Returns:
            (clamped_x, clamped_y): 限制后的坐标
        """
        center_x = frame_width / 2
        center_y = frame_height / 2

        # 计算允许的最大偏移量
        max_offset_x = frame_width * self.max_horizontal_offset
        max_offset_y = frame_height * self.max_vertical_offset

        # 限制坐标
        clamped_x = max(center_x - max_offset_x, min(center_x + max_offset_x, x))
        clamped_y = max(center_y - max_offset_y, min(center_y + max_offset_y, y))

        return clamped_x, clamped_y

    def detect_objects(self, frame):
        """
        使用 YOLO 检测物体（只检测目标类别）

        Args:
            frame: 输入图像

        Returns:
            detections: 检测结果列表 [(x1, y1, x2, y2, conf, class_id), ...]
                        只包含目标类别的检测
        """
        if self.model is None:
            return []

        # 获取目标类别ID
        target_id = None
        for class_id, class_name in self.class_names.items():
            if class_name == self.target_class:
                target_id = class_id
                break

        # 只检测目标类别（使用 classes 参数过滤）
        if target_id is not None:
            results = self.model(frame, conf=self.conf_threshold, iou=self.iou_threshold,
                               classes=[target_id], verbose=False)
        else:
            # 如果目标类别不存在，检测所有类别
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
        过滤出目标类别的检测（现已废弃，检测时已过滤）

        保留此方法以保持兼容性，直接返回输入
        """
        return detections

    def select_best_target(self, detections, frame_width, frame_height):
        """
        从检测结果中选择最佳追踪目标

        策略：优先选择最接近中心的检测框

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
            det_center_x = (x1 + x2) / 2
            det_center_y = (y1 + y2) / 2

            distance = math.sqrt((det_center_x - center_x) ** 2 + (det_center_y - center_y) ** 2)

            if distance < min_distance:
                min_distance = distance
                best_detection = det

        return best_detection

    def update_control(self, detection, frame_width, frame_height, current_time):
        """
        根据检测结果更新控制

        核心思想：让机器人转向看向检测到的目标位置
        随着机器人转向，目标会在图像中移动到中心位置

        Args:
            detection: 检测结果 (x1, y1, x2, y2, conf, class_id)
            frame_width, frame_height: 帧尺寸
            current_time: 当前时间戳
        """
        x1, y1, x2, y2, conf, class_id = detection

        # 计算检测框中心（这是目标在图像中的实际位置）
        det_center_x = (x1 + x2) / 2
        det_center_y = (y1 + y2) / 2

        # 归一化误差
        error_x, error_y = self.normalize_to_center(det_center_x, det_center_y, frame_width, frame_height)

        # 检查是否在死区内
        if abs(error_x) < self.dead_zone and abs(error_y) < self.dead_zone:
            return  # 在死区内，不调整

        # 应用平滑控制
        smooth_x, smooth_y = self.apply_smoothing(det_center_x, det_center_y)

        # 限制目标位置在安全范围内
        target_x, target_y = self.clamp_target_position(smooth_x, smooth_y, frame_width, frame_height)

        # 更新插值状态
        self.last_target_x = target_x
        self.last_target_y = target_y
        self.last_command_time = current_time

        # 执行头部运动 - 让机器人转向看向目标
        # 随着机器人转向，目标会移动到图像中心
        try:
            self.mini.look_at_image(int(target_x), int(target_y), duration=self.control_speed)
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

    def draw_crosshair(self, frame, x, y, size=20, color=(0, 255, 255)):
        """在指定位置绘制十字准星"""
        cv2.drawMarker(frame, (int(x), int(y)), color,
                      cv2.MARKER_CROSS, size, 2)

    def draw_safe_zone(self, frame, frame_width, frame_height):
        """绘制安全运动范围"""
        center_x = int(frame_width / 2)
        center_y = int(frame_height / 2)

        max_offset_x = int(frame_width * self.max_horizontal_offset)
        max_offset_y = int(frame_height * self.max_vertical_offset)

        # 绘制矩形边界
        top_left = (center_x - max_offset_x, center_y - max_offset_y)
        bottom_right = (center_x + max_offset_x, center_y + max_offset_y)
        cv2.rectangle(frame, top_left, bottom_right, (255, 255, 0), 1)

        # 绘制死区
        dead_zone_x = int(frame_width * self.dead_zone)
        dead_zone_y = int(frame_height * self.dead_zone)
        cv2.rectangle(frame,
                     (center_x - dead_zone_x, center_y - dead_zone_y),
                     (center_x + dead_zone_x, center_y + dead_zone_y),
                     (0, 255, 0), 1)

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

        # 检测所有物体（已过滤为只包含目标类别）
        detections = self.detect_objects(frame)

        # 过滤目标类别（现已废弃，直接返回）
        target_detections = self.filter_target_class(detections)

        # 选择最佳追踪目标
        target_detection = self.select_best_target(target_detections, width, height)

        # 更新追踪状态
        if target_detection is not None:
            self.is_tracking = True
            self.last_detection_time = current_time
            self.lost_track_count = 0

            # 更新控制（传入当前时间用于插值）
            self.update_control(target_detection, width, height, current_time)

            # 保存历史轨迹
            x1, y1, x2, y2, _, _ = target_detection
            self.center_history.append(((x1 + x2) / 2, (y1 + y2) / 2))
        else:
            self.lost_track_count += 1

            # 检查是否超时
            if current_time - self.last_detection_time > self.detection_timeout:
                self.is_tracking = False
                # 重置平滑状态
                self.smooth_x = None
                self.smooth_y = None
                # 重置插值状态
                self.last_target_x = None
                self.last_target_y = None
                self.last_command_time = None
                # 重置卡尔曼滤波器
                if self.kalman_tracker is not None:
                    self.kalman_tracker.reset()

        # 绘制安全区域和死区
        self.draw_safe_zone(frame, width, height)

        # 绘制检测结果
        annotated_frame = self.draw_detections(frame, detections, target_detection)

        # 绘制追踪状态
        status_text = f"Tracking V2: {'YES' if self.is_tracking else 'NO'}"
        status_color = (0, 255, 0) if self.is_tracking else (0, 0, 255)
        cv2.putText(annotated_frame, status_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

        # 绘制目标类别
        class_text = f"Target: {self.target_class}"
        cv2.putText(annotated_frame, class_text, (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 绘制平滑后的目标点（如果正在追踪）
        if self.is_tracking and self.smooth_x is not None:
            self.draw_crosshair(annotated_frame, self.smooth_x, self.smooth_y,
                              size=15, color=(255, 0, 255))

        # 绘制中心十字（黄色，表示期望目标到达的位置）
        center_x, center_y = width // 2, height // 2
        self.draw_crosshair(annotated_frame, center_x, center_y,
                           size=20, color=(0, 255, 255))

        # 绘制历史轨迹
        if len(self.center_history) > 1:
            points = [(int(p[0]), int(p[1])) for p in self.center_history]
            for i in range(1, len(points)):
                cv2.line(annotated_frame, points[i-1], points[i], (255, 0, 0), 2)

        return annotated_frame


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reachy Mini Object Tracking V2 - Full 2D Tracking"
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
        default=0.9,
        help='Window display scale (0.1 - 1.0), default 0.9 for larger window'
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
        '--smooth-factor',
        type=float,
        default=0.5,
        help='Smoothing factor (0.0-1.0), default 0.5 for faster response'
    )
    parser.add_argument(
        '--dead-zone',
        type=float,
        default=0.05,
        help='Dead zone ratio (0.0-1.0)'
    )
    parser.add_argument(
        '--control-speed',
        type=float,
        default=0.15,
        help='Control response speed (seconds), default 0.15 for faster response'
    )
    parser.add_argument(
        '--detection-timeout',
        type=float,
        default=1.0,
        help='Detection timeout before losing track (seconds)'
    )
    parser.add_argument(
        '--use-kalman',
        action='store_true',
        default=True,
        help='Use Kalman filter for smooth tracking (enabled by default)'
    )
    parser.add_argument(
        '--no-kalman',
        action='store_true',
        help='Disable Kalman filter'
    )
    parser.add_argument(
        '--kalman-process-noise',
        type=float,
        default=0.001,
        help='Kalman process noise (lower = smoother, default 0.001)'
    )
    parser.add_argument(
        '--kalman-measurement-noise',
        type=float,
        default=0.1,
        help='Kalman measurement noise (lower = trust measurement more, default 0.1)'
    )

    args = parser.parse_args()

    # 处理卡尔曼滤波器选项
    use_kalman = args.use_kalman and not args.no_kalman

    print("=" * 60)
    print("Reachy Mini Object Tracking V2 - Kalman Filter Edition")
    print("=" * 60)
    print(f"Target class: {args.target_class}")
    print(f"YOLO model: {args.model}")
    print(f"Confidence threshold: {args.conf_threshold}")
    print(f"Smooth factor: {args.smooth_factor}")
    print(f"Dead zone: {args.dead_zone}")
    print(f"Kalman Filter: {'Enabled' if use_kalman else 'Disabled'}")
    if use_kalman:
        print(f"  - Process noise: {args.kalman_process_noise}")
        print(f"  - Measurement noise: {args.kalman_measurement_noise}")
    print("=" * 60)
    print("\nV2 Features:")
    print("  - Full 2D tracking (Yaw + Pitch)")
    print("  - Kalman filter for smooth tracking")
    print("  - Safety limits applied")
    print("  - Only displays target class detections")
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

        # 初始化追踪器 V2
        tracker = ObjectTrackerV2(
            reachy_mini=reachy_mini,
            model_name=args.model,
            target_class=args.target_class,
            conf_threshold=args.conf_threshold,
            iou_threshold=args.iou_threshold,
            smooth_factor=args.smooth_factor,
            dead_zone=args.dead_zone,
            detection_timeout=args.detection_timeout,
            use_kalman=use_kalman,
            kalman_process_noise=args.kalman_process_noise,
            kalman_measurement_noise=args.kalman_measurement_noise,
        )
        tracker.control_speed = args.control_speed

        # 计算显示窗口大小
        display_width = int(width * window_scale)
        display_height = int(height * window_scale)
        print(f"Display window size: {display_width}x{display_height}")

        try:
            while True:
                # 获取摄像头画面
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
                cv2.imshow("Reachy Mini Object Tracking V2", display_frame)

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
