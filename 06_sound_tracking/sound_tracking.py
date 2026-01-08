"""
Reachy Mini 声源定位追踪演示 (Demo 6)

基于声源定位 (DoA) 的智能交互演示。Reachy Mini 会实时检测声源方向，
并自动转向说话的人，实现自然的听觉-视觉交互体验。

功能：
1. 实时声源定位 (DoA)
2. 自动追踪声源方向
3. PID 控制实现平滑运动
4. 多种追踪模式（头部/身体/混合）
5. 视觉反馈和状态显示
6. 天线交互反馈

前置条件：
    pip install reachy-mini opencv-python numpy

使用：
    # 默认模式：仅头部追踪
    python sound_tracking.py

    # 头部 + 身体追踪
    python sound_tracking.py --mode hybrid

    # 调整灵敏度
    python sound_tracking.py --sensitivity high

    # 调整响应速度
    python sound_tracking.py --speed 0.2
"""

import argparse
import time
import math
import sys
from collections import deque
from enum import Enum

import numpy as np
import cv2

try:
    from reachy_mini import ReachyMini
    from reachy_mini.utils import create_head_pose
    REACHY_AVAILABLE = True
except ImportError:
    REACHY_AVAILABLE = False
    print("Warning: reachy-mini not installed. Install with: pip install reachy-mini")


class TrackingMode(Enum):
    """追踪模式枚举"""
    HEAD = "head"      # 仅头部追踪
    BODY = "body"      # 仅身体追踪
    HYBRID = "hybrid"  # 头部 + 身体协调


class TrackingState(Enum):
    """追踪状态枚举"""
    IDLE = "idle"              # 待机
    DETECTING = "detecting"    # 检测中
    TRACKING = "tracking"      # 追踪中
    LOST = "lost"              # 声源丢失


class Sensitivity(Enum):
    """灵敏度设置"""
    LOW = (0.5, "低 - 适合安静环境")
    MEDIUM = (0.3, "中 - 一般环境")
    HIGH = (0.15, "高 - 嘈杂环境")

    def __init__(self, min_duration, description):
        self.min_duration = min_duration
        self.description = description


class PIDController:
    """PID 控制器 - 实现平滑运动"""

    def __init__(self, kp=0.6, ki=0.01, kd=0.3, output_limit=35.0):
        """
        初始化 PID 控制器

        Args:
            kp: 比例系数
            ki: 积分系数
            kd: 微分系数
            output_limit: 输出限幅（度）
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = output_limit

        # 状态变量
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.time()

    def update(self, setpoint, measured_value):
        """
        更新 PID 控制器

        Args:
            setpoint: 目标值（度）
            measured_value: 当前测量值（度）

        Returns:
            控制输出（度）
        """
        current_time = time.time()
        dt = current_time - self.last_time

        if dt <= 0:
            return 0.0

        # 计算误差
        error = setpoint - measured_value

        # 比例项
        p_term = self.kp * error

        # 积分项（带抗饱和）
        self.integral += error * dt
        # 限制积分项
        integral_limit = self.output_limit / (self.ki if self.ki > 0 else 1)
        self.integral = np.clip(self.integral, -integral_limit, integral_limit)
        i_term = self.ki * self.integral

        # 微分项
        if dt > 0:
            derivative = (error - self.last_error) / dt
            d_term = self.kd * derivative
        else:
            d_term = 0.0

        # 计算输出
        output = p_term + i_term + d_term

        # 限幅
        output = np.clip(output, -self.output_limit, self.output_limit)

        # 更新状态
        self.last_error = error
        self.last_time = current_time

        return output

    def reset(self):
        """重置控制器状态"""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.time()


class VoiceActivityDetector:
    """语音活动检测 - 过滤短暂噪声"""

    def __init__(self, min_duration=0.3, cooldown=0.5):
        """
        初始化 VAD

        Args:
            min_duration: 最小语音持续时间（秒）
            cooldown: 检测后冷却时间（秒）
        """
        self.min_duration = min_duration
        self.cooldown = cooldown

        self.speech_start_time = None
        self.last_detection_time = 0
        self.in_cooldown = False

    def update(self, speech_detected):
        """
        更新 VAD 状态

        Args:
            speech_detected: 是否检测到语音

        Returns:
            是否应该触发追踪
        """
        current_time = time.time()

        # 检查冷却期
        if self.in_cooldown:
            if current_time - self.last_detection_time >= self.cooldown:
                self.in_cooldown = False
            else:
                return False

        # 处理语音检测
        if speech_detected:
            if self.speech_start_time is None:
                # 语音开始
                self.speech_start_time = current_time
            else:
                # 检查持续时间
                duration = current_time - self.speech_start_time
                if duration >= self.min_duration:
                    # 持续时间足够，触发追踪
                    self.last_detection_time = current_time
                    self.in_cooldown = True
                    self.speech_start_time = None
                    return True
        else:
            # 语音结束，重置
            self.speech_start_time = None

        return False


class SoundTracker:
    """声源追踪器主类"""

    def __init__(self, reachy_mini, mode=TrackingMode.HEAD, sensitivity=Sensitivity.MEDIUM,
                 control_speed=0.5, enable_antenna=True, pid_params=None):
        """
        初始化声源追踪器

        Args:
            reachy_mini: ReachyMini 实例
            mode: 追踪模式
            sensitivity: 灵敏度设置
            control_speed: 控制响应速度（秒）
            enable_antenna: 是否启用天线反馈
            pid_params: PID 参数字典
        """
        self.mini = reachy_mini
        self.mode = mode
        self.control_speed = control_speed
        self.enable_antenna = enable_antenna

        # VAD
        self.vad = VoiceActivityDetector(min_duration=sensitivity.min_duration)

        # PID 控制器
        pid_params = pid_params or {'kp': 0.6, 'ki': 0.01, 'kd': 0.3}
        output_limit = 160.0 if mode == TrackingMode.BODY else 35.0
        self.pid = PIDController(**pid_params, output_limit=output_limit)

        # 状态
        self.state = TrackingState.IDLE
        self.current_yaw = 0.0  # 当前角度（度）
        self.target_yaw = 0.0   # 目标角度（度）
        self.last_doa_angle = None
        self.last_detection_time = 0
        self.detection_timeout = 2.0  # 声源丢失超时

        # 天线状态
        self.antenna_rest = [0.0, 0.0]
        self.antenna_active = [0.5, 0.5]

        # 历史记录（用于显示）
        self.doa_history = deque(maxlen=50)
        self.yaw_history = deque(maxlen=100)

        # 统计信息
        self.stats = {
            'total_detections': 0,
            'tracking_activations': 0,
            'last_update_time': time.time()
        }

        print(f"追踪器配置:")
        print(f"  模式: {mode.value}")
        print(f"  灵敏度: {sensitivity.description}")
        print(f"  响应速度: {control_speed}s")
        print(f"  PID: Kp={pid_params['kp']}, Ki={pid_params['ki']}, Kd={pid_params['kd']}")

    def doa_to_robot_yaw(self, doa_angle_rad):
        """
        将 DoA 角度转换为机器人偏航角

        DoA 角度定义:
        - 0 弧度 = 左侧
        - π/2 弧度 = 前方
        - π 弧度 = 右侧

        机器人偏航:
        - 正值 = 左转
        - 负值 = 右转

        Args:
            doa_angle_rad: DoA 角度（弧度）

        Returns:
            机器人偏航角（度）
        """
        doa_deg = math.degrees(doa_angle_rad)

        # 转换：DoA 0°(左) -> 机器人 +90°, DoA 90°(前) -> 机器人 °
        robot_yaw = 90.0 - doa_deg

        # 归一化到 [-180, 180]
        robot_yaw = (robot_yaw + 180) % 360 - 180

        return robot_yaw

    def update(self, doa_result):
        """
        更新追踪器状态

        Args:
            doa_result: (angle, speech_detected) 元组或 None
        """
        current_time = time.time()

        # 处理 DoA 结果
        if doa_result is not None:
            doa_angle, speech_detected = doa_result

            # 记录历史
            self.doa_history.append({
                'time': current_time,
                'angle': doa_angle,
                'speech': speech_detected
            })

            self.stats['total_detections'] += 1

            # VAD 处理
            if self.vad.update(speech_detected):
                # 检测到有效语音
                self.last_detection_time = current_time
                self.last_doa_angle = doa_angle
                self.target_yaw = self.doa_to_robot_yaw(doa_angle)
                self.state = TrackingState.TRACKING
                self.stats['tracking_activations'] += 1

                # 天线反馈
                if self.enable_antenna:
                    self._set_antenna(self.antenna_active)

        # 检查超时
        if current_time - self.last_detection_time > self.detection_timeout:
            if self.state == TrackingState.TRACKING:
                self.state = TrackingState.LOST

                # 天线恢复
                if self.enable_antenna:
                    self._set_antenna(self.antenna_rest)

                # PID 重置
                self.pid.reset()

        # 执行控制
        if self.state == TrackingState.TRACKING:
            self._execute_control()

        # 更新统计
        self.stats['last_update_time'] = current_time

    def _execute_control(self):
        """执行运动控制"""
        # PID 计算输出
        pid_output = self.pid.update(self.target_yaw, self.current_yaw)

        # 更新当前角度（简单积分）
        self.current_yaw += pid_output

        # 限制范围
        if self.mode == TrackingMode.HEAD:
            self.current_yaw = np.clip(self.current_yaw, -35, 35)
        else:  # BODY or HYBRID
            self.current_yaw = np.clip(self.current_yaw, -160, 160)

        # 记录历史
        self.yaw_history.append({
            'time': time.time(),
            'yaw': self.current_yaw
        })

        # 执行运动
        try:
            if self.mode == TrackingMode.HEAD:
                # 仅头部
                pose = create_head_pose(yaw=self.current_yaw, degrees=True)
                self.mini.goto_target(head=pose, duration=self.control_speed)

            elif self.mode == TrackingMode.BODY:
                # 仅身体
                body_yaw_rad = math.radians(self.current_yaw)
                self.mini.goto_target(body_yaw=body_yaw_rad, duration=self.control_speed)

            else:  # HYBRID
                # 混合模式：头部和身体协调
                # 头部负责快速小幅运动，身体负责大幅运动
                head_limit = 25.0

                if abs(self.current_yaw) <= head_limit:
                    # 小角度：仅头部
                    pose = create_head_pose(yaw=self.current_yaw, degrees=True)
                    self.mini.goto_target(head=pose, duration=self.control_speed)
                else:
                    # 大角度：头部 + 身体
                    # 身体承担大部分
                    body_yaw = np.sign(self.current_yaw) * (abs(self.current_yaw) - head_limit)
                    body_yaw_rad = math.radians(body_yaw)

                    # 头部保持极限位置
                    head_yaw = np.sign(self.current_yaw) * head_limit
                    pose = create_head_pose(yaw=head_yaw, degrees=True)

                    self.mini.goto_target(
                        head=pose,
                        body_yaw=body_yaw_rad,
                        duration=self.control_speed
                    )

        except Exception as e:
            print(f"Error executing control: {e}")

    def _set_antenna(self, angles):
        """设置天线角度"""
        try:
            antenna_rad = [math.radians(a) for a in angles]
            self.mini.set_target(antennas=antenna_rad)
        except Exception as e:
            pass  # 忽略天线错误

    def reset(self):
        """重置追踪器"""
        self.state = TrackingState.IDLE
        self.current_yaw = 0.0
        self.target_yaw = 0.0
        self.pid.reset()
        self.vad.speech_start_time = None

        # 复位天线
        if self.enable_antenna:
            self._set_antenna(self.antenna_rest)

        # 复位位置
        try:
            if self.mode == TrackingMode.HEAD:
                self.mini.goto_target(
                    head=create_head_pose(yaw=0, degrees=True),
                    duration=1.0
                )
            else:
                self.mini.goto_target(body_yaw=0.0, duration=1.0)
        except Exception as e:
            print(f"Error resetting: {e}")


class Visualizer:
    """可视化界面"""

    def __init__(self, tracker, window_scale=0.7, show_camera=True):
        """
        初始化可视化

        Args:
            tracker: SoundTracker 实例
            window_scale: 窗口缩放比例
            show_camera: 是否显示摄像头画面
        """
        self.tracker = tracker
        self.window_scale = window_scale
        self.show_camera = show_camera

        self.window_width = int(800 * window_scale)
        self.window_height = int(600 * window_scale)

        # 颜色定义
        self.colors = {
            'idle': (128, 128, 128),       # 灰色
            'detecting': (0, 200, 255),    # 黄色
            'tracking': (0, 255, 0),       # 绿色
            'lost': (0, 0, 255),           # 红色
            'text': (255, 255, 255),
            'background': (20, 20, 30)
        }

    def draw_direction_indicator(self, img, center, radius, angle_deg):
        """绘制声源方向指示器"""
        # 转换角度（0° = 上，顺时针）
        indicator_angle = angle_deg - 90

        # 计算箭头位置
        rad = math.radians(indicator_angle)
        end_x = int(center[0] + radius * math.cos(rad))
        end_y = int(center[1] + radius * math.sin(rad))

        # 绘制圆圈
        cv2.circle(img, center, radius, (80, 80, 100), 2)

        # 绘制方向线
        cv2.line(img, center, (end_x, end_y), self.colors['tracking'], 3)

        # 绘制箭头
        arrow_size = 15
        arrow_angle1 = math.radians(indicator_angle + 150)
        arrow_angle2 = math.radians(indicator_angle - 150)

        arrow1_x = end_x + arrow_size * math.cos(arrow_angle1)
        arrow1_y = end_y + arrow_size * math.sin(arrow_angle1)
        arrow2_x = end_x + arrow_size * math.cos(arrow_angle2)
        arrow2_y = end_y + arrow_size * math.sin(arrow_angle2)

        cv2.line(img, (end_x, end_y), (int(arrow1_x), int(arrow1_y)),
                 self.colors['tracking'], 3)
        cv2.line(img, (end_x, end_y), (int(arrow2_x), int(arrow2_y)),
                 self.colors['tracking'], 3)

        # 绘制中心点
        cv2.circle(img, center, 5, (255, 255, 0), -1)

    def draw_info_panel(self, img):
        """绘制信息面板"""
        y_offset = 20
        line_height = 25

        # 状态颜色
        state = self.tracker.state
        state_color = self.colors.get(state.value, self.colors['idle'])

        # 标题
        cv2.putText(img, "Reachy Mini Sound Tracking",
                   (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX,
                   0.7, self.colors['text'], 2)
        y_offset += line_height * 1.5

        # 状态
        state_text = f"State: {state.value.upper()}"
        cv2.putText(img, state_text, (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, state_color, 2)
        y_offset += line_height

        # 目标角度
        target_text = f"Target: {self.tracker.target_yaw:.1f}"
        cv2.putText(img, target_text, (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
        y_offset += line_height

        # 当前角度
        current_text = f"Current: {self.tracker.current_yaw:.1f}"
        cv2.putText(img, current_text, (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
        y_offset += line_height

        # DoA 角度
        if self.tracker.last_doa_angle is not None:
            doa_deg = math.degrees(self.tracker.last_doa_angle)
            doa_text = f"DoA: {doa_deg:.1f}"
            cv2.putText(img, doa_text, (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['text'], 1)
            y_offset += line_height

        # 统计信息
        y_offset += line_height // 2
        stats = self.tracker.stats
        detections_text = f"Detections: {stats['total_detections']}"
        cv2.putText(img, detections_text, (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        y_offset += line_height

        activations_text = f"Tracking: {stats['tracking_activations']}"
        cv2.putText(img, activations_text, (20, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    def draw(self, camera_frame=None):
        """
        绘制可视化界面

        Args:
            camera_frame: 摄像头画面（可选）
        """
        # 创建画布
        if camera_frame is not None and self.show_camera:
            img = camera_frame.copy()
        else:
            img = np.full((self.window_height, self.window_width, 3),
                         self.colors['background'], dtype=np.uint8)

        # 绘制信息面板
        self.draw_info_panel(img)

        # 绘制方向指示器
        center = (self.window_width - 100, 100)
        radius = 60

        if self.tracker.state == TrackingState.TRACKING:
            self.draw_direction_indicator(img, center, radius, self.tracker.target_yaw)
        else:
            # 空闲状态显示圆圈
            cv2.circle(img, center, radius, (80, 80, 100), 2)
            cv2.circle(img, center, 5, (128, 128, 128), -1)

        # 绘制控制提示
        hint_y = self.window_height - 30
        cv2.putText(img, "Press 'q' to quit | 'r' to reset",
                   (20, hint_y), cv2.FONT_HERSHEY_SIMPLEX,
                   0.4, (100, 100, 100), 1)

        # 调整大小
        if self.window_scale != 1.0:
            new_width = int(img.shape[1] * self.window_scale)
            new_height = int(img.shape[0] * self.window_scale)
            img = cv2.resize(img, (new_width, new_height))

        return img


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reachy Mini 声源定位追踪演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 默认模式：仅头部追踪
  python sound_tracking.py

  # 头部 + 身体追踪
  python sound_tracking.py --mode hybrid

  # 高灵敏度
  python sound_tracking.py --sensitivity high

  # 快速响应
  python sound_tracking.py --speed 0.2
        """
    )

    parser.add_argument(
        '--mode',
        type=str,
        default='head',
        choices=['head', 'body', 'hybrid'],
        help='追踪模式'
    )
    parser.add_argument(
        '--backend',
        type=str,
        default='default',
        choices=['default', 'gstreamer', 'webrtc'],
        help='媒体后端'
    )
    parser.add_argument(
        '--sensitivity',
        type=str,
        default='medium',
        choices=['low', 'medium', 'high'],
        help='灵敏度'
    )
    parser.add_argument(
        '--speed',
        type=float,
        default=0.5,
        help='响应速度（秒）'
    )
    parser.add_argument(
        '--window-scale',
        type=float,
        default=0.7,
        help='窗口缩放比例（0.1-1.0）'
    )
    parser.add_argument(
        '--no-antenna',
        action='store_true',
        help='禁用天线反馈'
    )
    parser.add_argument(
        '--no-camera',
        action='store_true',
        help='不显示摄像头画面'
    )
    parser.add_argument(
        '--pid-p',
        type=float,
        default=0.6,
        help='PID 比例系数'
    )
    parser.add_argument(
        '--pid-i',
        type=float,
        default=0.01,
        help='PID 积分系数'
    )
    parser.add_argument(
        '--pid-d',
        type=float,
        default=0.3,
        help='PID 微分系数'
    )
    parser.add_argument(
        '--min-duration',
        type=float,
        default=0.3,
        help='最小语音持续时间（秒）'
    )

    args = parser.parse_args()

    # 检查依赖
    if not REACHY_AVAILABLE:
        print("Error: reachy-mini 未安装")
        print("请安装: pip install reachy-mini")
        sys.exit(1)

    print("=" * 60)
    print("Reachy Mini 声源定位追踪演示")
    print("=" * 60)

    # 解析参数
    mode = TrackingMode(args.mode)
    sensitivity = {
        'low': Sensitivity.LOW,
        'medium': Sensitivity.MEDIUM,
        'high': Sensitivity.HIGH
    }[args.sensitivity]

    # 覆盖最小持续时间
    if args.min_duration != 0.3:
        # 创建自定义灵敏度
        sensitivity = Sensitivity(args.min_duration, "自定义")

    pid_params = {
        'kp': args.pid_p,
        'ki': args.pid_i,
        'kd': args.pid_d
    }

    # 连接机器人
    print("\n正在连接到 Reachy Mini...")
    try:
        with ReachyMini(media_backend=args.backend) as reachy_mini:
            print("连接成功！")

            # 创建追踪器
            tracker = SoundTracker(
                reachy_mini,
                mode=mode,
                sensitivity=sensitivity,
                control_speed=args.speed,
                enable_antenna=not args.no_antenna,
                pid_params=pid_params
            )

            # 创建可视化
            visualizer = Visualizer(
                tracker,
                window_scale=args.window_scale,
                show_camera=not args.no_camera
            )

            print("\n开始追踪...")
            print("按 'q' 退出，'r' 重置\n")

            # 主循环
            try:
                while True:
                    # 获取 DoA 数据
                    doa_result = reachy_mini.media.get_DoA()

                    # 更新追踪器
                    tracker.update(doa_result)

                    # 获取摄像头画面（如果需要）
                    camera_frame = None
                    if not args.no_camera:
                        try:
                            camera_frame = reachy_mini.media.get_frame()
                            if camera_frame is not None:
                                camera_frame = cv2.cvtColor(camera_frame,
                                                           cv2.COLOR_BGR2RGB)
                        except Exception:
                            pass

                    # 绘制界面
                    display_img = visualizer.draw(camera_frame)

                    # 显示
                    cv2.imshow('Reachy Mini Sound Tracking',
                              cv2.cvtColor(display_img, cv2.COLOR_RGB2BGR))

                    # 键盘控制
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("\n退出程序...")
                        break
                    elif key == ord('r'):
                        print("\n重置追踪器...")
                        tracker.reset()

            except KeyboardInterrupt:
                print("\n\n程序已中断")

            # 重置机器人
            print("\n重置机器人位置...")
            tracker.reset()
            time.sleep(1)

            cv2.destroyAllWindows()

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
