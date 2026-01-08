"""
Reachy Mini YOLO 物体追踪 - 头部 Pitch + Yaw 双轴追踪版本

使用 YOLO 检测指定物体，使用头部 Pitch 和 Yaw 进行双轴物体追踪。

功能：
1. 使用 YOLO 检测指定类别物体
2. 使用位置滤波器平滑坐标波动
3. 使用 PID 控制器计算头部 Pitch 和 Yaw 调整量
4. 控制头部使目标保持在视野中心

控制策略：
- 垂直方向: 使用头部 Pitch 旋转
- 水平方向: 使用头部 Yaw 旋转

前置条件：
    pip install reachy-mini opencv-python ultralytics

使用：
    python track_object.py --class bottle
    python track_object.py --class cup --pid-p 1.5 --conf-threshold 0.7
"""

import argparse
import math
import time

import cv2

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

from yolo_detector import YoloDetector
from position_filter import PositionFilter
from head_yaw_controller import HeadYawController


class HeadPitchController:
    """头部 Pitch 控制器 - PID 控制"""

    def __init__(self, pid_p=0.5, pid_i=0.0, pid_d=0.0, pitch_limit=35, dead_zone=0.05):
        """
        初始化控制器

        Args:
            pid_p: 比例系数
            pid_i: 积分系数
            pid_d: 微分系数
            pitch_limit: Pitch 角度限制（度）
            dead_zone: 死区比例（目标在中央此范围内时不调整）
        """
        self.pid_p = pid_p
        self.pid_i = pid_i
        self.pid_d = pid_d
        self.gain = 0.08  # 增益系数，可通过滑条动态调整
        self.pitch_limit = math.radians(pitch_limit)
        self.dead_zone = dead_zone

        # 当前状态
        self.current_pitch = 0.0

        # PID 状态
        self.integral = 0.0
        self.last_error = 0.0

    def normalize_to_center(self, y, frame_height):
        """
        将图像 y 坐标归一化到中心坐标系

        Args:
            y: 图像 y 坐标
            frame_height: 帧高度

        Returns:
            norm_y: 归一化坐标，范围 [-1, 1]，0 表示中心
        """
        center_y = frame_height / 2
        norm_y = (y - center_y) / center_y
        return norm_y

    def compute(self, target_y, frame_height, dt):
        """
        计算控制输出

        Args:
            target_y: 目标 y 坐标
            frame_height: 帧高度
            dt: 时间步长

        Returns:
            new_pitch: 新的头部 Pitch 角度（弧度）
        """
        # 归一化误差
        error = self.normalize_to_center(target_y, frame_height)

        # 检查死区
        if abs(error) < self.dead_zone:
            return self.current_pitch

        # PID 计算
        # 比例项
        p = self.pid_p * error

        # 积分项
        self.integral += error * dt
        self.integral = max(-1.0, min(1.0, self.integral))
        i = self.pid_i * self.integral

        # 微分项
        d = 0.0
        if dt > 0:
            d = self.pid_d * (error - self.last_error) / dt
        self.last_error = error

        # 控制输出
        control = p + i + d
        control = max(-1.0, min(1.0, control))

        # 计算新的头部 Pitch 角度
        # 图像坐标系：y 向下增大（从上到下）
        # 实际测试结果：
        #   S键（抬头，负Pitch）→ 物体向上移动 → y减小
        #   W键（低头，正Pitch）→ 物体向下移动 → y增大
        #
        # 追踪目标：让物体中心移动到画面中心
        #   目标在上方（y < center, error < 0）→ 需要抬头（负Pitch）→ 物体会向下移到中心
        #   目标在下方（y > center, error > 0）→ 需要低头（正Pitch）→ 物体会向上移到中心
        #
        # 因此：error < 0 需要负调整，error > 0 需要正调整
        # 直接使用 control（不带负号），使用动态增益
        pitch_adjustment = control * self.gain  # 使用动态增益
        new_pitch = self.current_pitch + pitch_adjustment

        # 限制范围
        new_pitch = max(-self.pitch_limit, min(self.pitch_limit, new_pitch))

        return new_pitch

    def update(self, new_pitch):
        """更新当前 Pitch 状态"""
        self.current_pitch = new_pitch

    def reset(self):
        """重置控制器状态"""
        self.current_pitch = 0.0
        self.integral = 0.0
        self.last_error = 0.0


class YoloObjectTracker:
    """YOLO 物体追踪器"""

    def __init__(self, reachy_mini, model_name='yolov8n.pt', target_class='bottle',
                 conf_threshold=0.5, iou_threshold=0.45,
                 pid_p=1.0, pid_i=0.0, pid_d=0.1,
                 filter_window_size=5, filter_jump_threshold=30):
        """
        初始化追踪器

        Args:
            reachy_mini: ReachyMini 实例
            model_name: YOLO 模型名称
            target_class: 目标类别名称
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值
            pid_p: PID 比例系数
            pid_i: PID 积分系数
            pid_d: PID 微分系数
            filter_window_size: 位置滤波器窗口大小
            filter_jump_threshold: 位置滤波器跳变阈值
        """
        self.mini = reachy_mini

        # YOLO 检测器
        self.detector = YoloDetector(
            model_name=model_name,
            target_class=target_class,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold
        )

        # 位置滤波器
        self.filter = PositionFilter(
            window_size=filter_window_size,
            jump_threshold=filter_jump_threshold
        )

        # 头部 Pitch 控制器（垂直方向）
        self.pitch_controller = HeadPitchController(
            pid_p=pid_p,
            pid_i=pid_i,
            pid_d=pid_d
        )

        # 手动控制状态
        self.manual_pitch = 0.0  # 当前手动 Pitch 值（度）
        self.manual_yaw = 0.0  # 当前手动 Yaw 值（度）
        self.manual_mode = False  # 自动模式（已关闭手动）

        # 头部 Yaw 控制器（水平方向）
        self.yaw_controller = HeadYawController(
            pid_p=pid_p,
            pid_i=pid_i,
            pid_d=pid_d
        )

        # 追踪状态
        self.is_tracking = False
        self.last_detection_time = 0
        self.detection_timeout = 1.0

        self.target_class = target_class

    def process_frame(self, frame):
        """
        处理一帧图像

        Args:
            frame: 输入图像

        Returns:
            annotated_frame: 绘制了结果的图像
            target_x: 滤波后的目标 x 坐标，如果没有检测到则为 None
            detection: 目标检测结果，如果没有检测到则为 None
            area: 目标面积
        """
        height, width = frame.shape[:2]
        current_time = time.time()
        dt = current_time - self.last_detection_time if self.last_detection_time > 0 else 0.03

        # YOLO 检测
        detections = self.detector.detect(frame)

        # 查找目标中心
        center, detection, area = self.detector.find_target_center(detections, width, height)

        target_x = None

        if center is not None:
            self.is_tracking = True
            self.last_detection_time = current_time

            # 位置滤波
            filtered_x, filtered_y = self.filter.filter(center[0], center[1])
            target_x = filtered_x

            # ========== 手动模式 - 不自动控制 ==========
            if self.manual_mode:
                # 只检测，不控制
                pass
            else:
                # ========== Pitch 控制（垂直方向）==========
                new_pitch = self.pitch_controller.compute(filtered_y, height, dt)
                self.pitch_controller.update(new_pitch)

                # ========== Yaw 控制（水平方向）==========
                new_yaw = self.yaw_controller.compute(filtered_x, width, dt)
                self.yaw_controller.update(new_yaw)

                # 发送控制指令（同时控制 Pitch 和 Yaw）
                self.send_control(new_pitch, new_yaw)

        else:
            # 检查是否超时
            if current_time - self.last_detection_time > self.detection_timeout:
                self.is_tracking = False
                self.pitch_controller.reset()
                self.yaw_controller.reset()
                self.filter.reset()

        # 绘制结果
        annotated_frame = self.draw_results(frame, detection, center, area)

        return annotated_frame, target_x, detection, area, center

    def send_control(self, head_pitch, head_yaw):
        """
        发送控制指令到机器人

        Args:
            head_pitch: 头部 Pitch 角度（弧度）
            head_yaw: 头部 Yaw 角度（弧度）
        """
        try:
            # 创建头部姿态（同时使用 Pitch 和 Yaw）
            head_pose = create_head_pose(
                x=0, y=0, z=0,
                roll=0,
                pitch=math.degrees(head_pitch),
                yaw=math.degrees(head_yaw),
                degrees=True,
                mm=True
            )

            # 发送控制指令（只控制头部，不控制身体）
            self.mini.set_target(
                head=head_pose,
                antennas=None,
                body_yaw=None
            )

        except Exception as e:
            print(f"Error sending control: {e}")

    def manual_control(self, pitch_delta, yaw_delta=0):
        """
        手动控制 Pitch 和 Yaw

        Args:
            pitch_delta: Pitch 变化量（度），负=抬头，正=低头
            yaw_delta: Yaw 变化量（度），负=左转，正=右转
        """
        self.manual_pitch += pitch_delta
        self.manual_yaw += yaw_delta
        # 限制在安全范围内
        self.manual_pitch = max(-40, min(40, self.manual_pitch))
        self.manual_yaw = max(-160, min(160, self.manual_yaw))

        try:
            head_pose = create_head_pose(
                x=0, y=0, z=0,
                roll=0,
                pitch=self.manual_pitch,
                yaw=self.manual_yaw,
                degrees=True,
                mm=True
            )
            self.mini.set_target(
                head=head_pose,
                antennas=None,
                body_yaw=None
            )
        except Exception as e:
            print(f"Error in manual control: {e}")

    def draw_results(self, frame, detection, center, area):
        """
        在图像上绘制结果

        Args:
            frame: 输入图像
            detection: YOLO 检测结果
            center: 目标中心
            area: 目标面积

        Returns:
            annotated_frame: 绘制了结果的图像
        """
        annotated_frame = frame.copy()
        height, width = annotated_frame.shape[:2]
        center_x = width // 2
        center_y = height // 2

        # ========== 绘制图像坐标系 ==========
        # 图像坐标系原点在左上角，x 向右，y 向下
        axis_length = 80
        axis_origin = (center_x - 100, center_y + 80)

        # X 轴（红色，向右）
        cv2.arrowedLine(annotated_frame, axis_origin,
                       (axis_origin[0] + axis_length, axis_origin[1]),
                       (0, 0, 255), 3, tipLength=0.3)
        cv2.putText(annotated_frame, "X+", (axis_origin[0] + axis_length + 5, axis_origin[1] + 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Y 轴（蓝色，向下）
        cv2.arrowedLine(annotated_frame, axis_origin,
                       (axis_origin[0], axis_origin[1] + axis_length),
                       (255, 0, 0), 3, tipLength=0.3)
        cv2.putText(annotated_frame, "Y+", (axis_origin[0] - 20, axis_origin[1] + axis_length + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # 坐标系标签
        cv2.putText(annotated_frame, "Image Coordinates", (axis_origin[0] - 30, axis_origin[1] - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # ========== 绘制中心十字准星（黄色）==========
        cv2.line(annotated_frame, (center_x - 60, center_y),
                (center_x + 60, center_y), (0, 255, 255), 3)
        cv2.line(annotated_frame, (center_x, center_y - 60),
                (center_x, center_y + 60), (0, 255, 255), 3)
        cv2.circle(annotated_frame, (center_x, center_y), 20, (0, 255, 255), 2)

        # ========== 绘制死区圆圈（绿色）==========
        dead_zone_radius = int(width * self.pitch_controller.dead_zone)
        cv2.circle(annotated_frame, (center_x, center_y), dead_zone_radius,
                  (0, 255, 0), 1, cv2.LINE_AA)

        if detection is not None and center is not None:
            x1, y1, x2, y2, conf, class_id = detection
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # 获取滤波后的坐标
            filtered_x, _ = self.filter.filter(center[0], center[1])

            # 绘制检测框（绿色）
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # 绘制原始检测点（白色小圆）
            cv2.circle(annotated_frame, (int(center[0]), int(center[1])), 5, (255, 255, 255), -1)

            # 绘制滤波后中心（绿色大圆）
            cv2.circle(annotated_frame, (int(filtered_x), int(center[1])), 12, (0, 255, 0), -1)
            cv2.circle(annotated_frame, (int(filtered_x), int(center[1])), 18, (255, 255, 255), 2)

            # 绘制到中心的连线
            cv2.line(annotated_frame, (int(filtered_x), int(center[1])),
                    (center_x, center_y), (0, 255, 0), 2)

            # 显示标签
            label = f"{self.target_class}: {conf:.2f}"
            cv2.putText(annotated_frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # 显示坐标和面积
            coord_text = f"X: {int(center[0])}"
            area_text = f"Area: {area:.0f}"
            offset_text = f"Offset: {int(filtered_x - center_x)}"

            cv2.putText(annotated_frame, coord_text, (int(filtered_x) + 25, int(center[1]) - 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(annotated_frame, area_text, (int(filtered_x) + 25, int(center[1])),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(annotated_frame, offset_text, (int(filtered_x) + 25, int(center[1]) + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return annotated_frame


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reachy Mini YOLO Object Tracking - Head Yaw"
    )
    parser.add_argument('--backend', type=str, default='default',
                       help='Media backend to use')
    parser.add_argument('--resolution', type=str, default='1280x960',
                       help='Camera resolution')
    parser.add_argument('--window-scale', type=float, default=0.6,
                       help='Window display scale (0.1 - 1.0)')
    parser.add_argument('--model', type=str, default='yolov8n.pt',
                       help='YOLO model name')
    parser.add_argument('--class', type=str, default='bottle',
                       dest='target_class',
                       help='Target object class to track')
    parser.add_argument('--conf-threshold', type=float, default=0.3,
                       help='Confidence threshold')
    parser.add_argument('--iou-threshold', type=float, default=0.45,
                       help='IOU threshold')
    parser.add_argument('--pid-p', type=float, default=0.5,
                       help='PID proportional gain')
    parser.add_argument('--pid-i', type=float, default=0.0,
                       help='PID integral gain')
    parser.add_argument('--pid-d', type=float, default=0.0,
                       help='PID derivative gain')
    parser.add_argument('--filter-window-size', type=int, default=5,
                       help='Position filter window size')
    parser.add_argument('--filter-jump-threshold', type=int, default=30,
                       help='Position filter jump threshold')

    args = parser.parse_args()

    print("=" * 60)
    print("Reachy Mini YOLO Object Tracking - Head Pitch")
    print("=" * 60)
    print(f"控制策略: 头部 Pitch (垂直方向) - Yaw 已禁用")
    print(f"目标类别: {args.target_class}")
    print(f"YOLO 模型: {args.model}")
    print(f"置信度阈值: {args.conf_threshold}")
    print(f"PID 参数: P={args.pid_p}, I={args.pid_i}, D={args.pid_d}")
    print("=" * 60)
    print("\n启动追踪...")
    print("按 'q' 退出\n")

    # 解析分辨率
    try:
        width, height = map(int, args.resolution.split('x'))
    except ValueError:
        width, height = 640, 480

    window_scale = max(0.1, min(1.0, args.window_scale))

    with ReachyMini(media_backend=args.backend) as reachy_mini:
        # 设置摄像头分辨率
        try:
            reachy_mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            reachy_mini.media.camera.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            print(f"摄像头分辨率: {width}x{height}")
        except Exception as e:
            print(f"警告: 无法设置分辨率: {e}")

        # 初始化追踪器
        tracker = YoloObjectTracker(
            reachy_mini=reachy_mini,
            model_name=args.model,
            target_class=args.target_class,
            conf_threshold=args.conf_threshold,
            iou_threshold=args.iou_threshold,
            pid_p=args.pid_p,
            pid_i=args.pid_i,
            pid_d=args.pid_d,
            filter_window_size=args.filter_window_size,
            filter_jump_threshold=args.filter_jump_threshold
        )

        # 检查 YOLO 是否可用
        if not tracker.detector.available:
            print("\n错误: YOLO 不可用，请安装 ultralytics")
            print("安装命令: pip install ultralytics")
            return

        display_width = int(width * window_scale)
        display_height = int(height * window_scale)
        print(f"显示窗口大小: {display_width}x{display_height}\n")
        print("自动追踪模式 (Pitch + Yaw 双轴追踪):")
        print("  W/S - 手动 Pitch 调整")
        print("  A/D - 手动 Yaw 调整")
        print("  Axis 滑条 - 切换调整哪个轴 (0=Pitch, 1=Yaw)")
        print("  PID 滑条 - 调整当前选中轴的参数")
        print("  Q - 退出\n")

        # 创建滑条窗口
        window_name = f"YOLO Object Tracking - {args.target_class}"
        cv2.namedWindow(window_name)

        # 轴切换开关 (0=Pitch, 1=Yaw)
        cv2.createTrackbar("Axis", window_name, 0, 1, lambda x: None)

        # 创建 PID 滑条（通过 Switch 切换调整哪个轴）
        cv2.createTrackbar("P Gain", window_name, int(args.pid_p * 100), 400, lambda x: None)
        cv2.createTrackbar("I Gain", window_name, int(args.pid_i * 100), 100, lambda x: None)
        cv2.createTrackbar("D Gain", window_name, int(args.pid_d * 100), 100, lambda x: None)
        cv2.createTrackbar("Speed", window_name, int(tracker.pitch_controller.gain * 100), 400, lambda x: None)

        try:
            while True:
                # 读取轴切换开关 (0=Pitch, 1=Yaw)
                axis_switch = cv2.getTrackbarPos("Axis", window_name)

                # 从滑条读取 PID 参数
                p_gain = cv2.getTrackbarPos("P Gain", window_name) / 100.0
                i_gain = cv2.getTrackbarPos("I Gain", window_name) / 100.0
                d_gain = cv2.getTrackbarPos("D Gain", window_name) / 100.0
                speed_gain = cv2.getTrackbarPos("Speed", window_name) / 100.0

                # 根据开关状态，更新对应轴的参数
                if axis_switch == 0:  # Pitch
                    tracker.pitch_controller.pid_p = p_gain
                    tracker.pitch_controller.pid_i = i_gain
                    tracker.pitch_controller.pid_d = d_gain
                    tracker.pitch_controller.gain = speed_gain
                else:  # Yaw
                    tracker.yaw_controller.pid_p = p_gain
                    tracker.yaw_controller.pid_i = i_gain
                    tracker.yaw_controller.pid_d = d_gain
                    tracker.yaw_controller.gain = speed_gain

                # 获取摄像头画面
                frame = reachy_mini.media.get_frame()
                if frame is None:
                    continue

                # 处理帧
                annotated_frame, target_x, detection, area, center = tracker.process_frame(frame)

                # 绘制状态信息
                status_text = f"Tracking: {'YES' if tracker.is_tracking else 'NO'}"
                status_color = (0, 255, 0) if tracker.is_tracking else (0, 0, 255)
                cv2.putText(annotated_frame, status_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)

                target_text = f"Target: {args.target_class}"
                cv2.putText(annotated_frame, target_text, (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # 显示当前 Pitch 和 Yaw
                pitch_deg = tracker.manual_pitch if tracker.manual_mode else math.degrees(tracker.pitch_controller.current_pitch)
                yaw_deg = math.degrees(tracker.yaw_controller.current_yaw)
                pitch_text = f"Pitch: {pitch_deg:.1f}° / [-40°, +40°]"
                yaw_text = f"Yaw: {yaw_deg:.1f}° / [-160°, +160°]"
                cv2.putText(annotated_frame, pitch_text, (10, 100),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                cv2.putText(annotated_frame, yaw_text, (10, 125),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                # 显示目标位置
                if center is not None:
                    target_pos_text = f"Target: ({int(center[0])}, {int(center[1])})"
                    cv2.putText(annotated_frame, target_pos_text, (10, 150),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # 显示模式
                mode_text = f"Mode: {'MANUAL' if tracker.manual_mode else 'AUTO'}"
                mode_color = (0, 255, 255) if tracker.manual_mode else (255, 0, 255)
                cv2.putText(annotated_frame, mode_text, (10, 175),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)

                # 显示控制提示
                help_text = "WASD: Manual | Axis(0=P/1=Y): Switch"
                cv2.putText(annotated_frame, help_text, (10, 200),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                # 显示 Pitch PID 参数
                pitch_pid_text = f"Pitch PID: P={tracker.pitch_controller.pid_p:.2f} I={tracker.pitch_controller.pid_i:.2f} D={tracker.pitch_controller.pid_d:.2f}"
                cv2.putText(annotated_frame, pitch_pid_text, (10, 225),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 200, 255), 1)

                pitch_gain_text = f"Pitch Gain: {tracker.pitch_controller.gain:.2f}"
                cv2.putText(annotated_frame, pitch_gain_text, (10, 245),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 200, 255), 1)

                # 显示 Yaw PID 参数
                yaw_pid_text = f"Yaw PID: P={tracker.yaw_controller.pid_p:.2f} I={tracker.yaw_controller.pid_i:.2f} D={tracker.yaw_controller.pid_d:.2f}"
                cv2.putText(annotated_frame, yaw_pid_text, (10, 270),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 150, 0), 1)

                yaw_gain_text = f"Yaw Gain: {tracker.yaw_controller.gain:.2f}"
                cv2.putText(annotated_frame, yaw_gain_text, (10, 290),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 150, 0), 1)

                # 显示当前选择的轴
                axis_text = f"Adjusting: {'PITCH' if axis_switch == 0 else 'YAW'}"
                axis_color = (100, 200, 255) if axis_switch == 0 else (255, 150, 0)
                cv2.putText(annotated_frame, axis_text, (10, 315),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, axis_color, 2)

                # 缩放显示
                if window_scale != 1.0:
                    display_frame = cv2.resize(annotated_frame, (display_width, display_height))
                else:
                    display_frame = annotated_frame

                cv2.imshow(window_name, display_frame)

                # 键盘控制
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n退出...")
                    break
                elif key == ord('w'):
                    tracker.manual_control(2, 0)  # 低头 2 度
                    print(f"Pitch: {tracker.manual_pitch:.1f}°, Yaw: {tracker.manual_yaw:.1f}°")
                elif key == ord('s'):
                    tracker.manual_control(-2, 0)  # 抬头 2 度
                    print(f"Pitch: {tracker.manual_pitch:.1f}°, Yaw: {tracker.manual_yaw:.1f}°")
                elif key == ord('a'):
                    tracker.manual_control(0, -2)  # 左转 2 度
                    print(f"Pitch: {tracker.manual_pitch:.1f}°, Yaw: {tracker.manual_yaw:.1f}°")
                elif key == ord('d'):
                    tracker.manual_control(0, 2)  # 右转 2 度
                    print(f"Pitch: {tracker.manual_pitch:.1f}°, Yaw: {tracker.manual_yaw:.1f}°")

        except KeyboardInterrupt:
            print("\n中断，关闭...")
        finally:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
