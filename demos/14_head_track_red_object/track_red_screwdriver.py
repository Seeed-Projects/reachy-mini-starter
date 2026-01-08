#!/usr/bin/env python3
"""Reachy Mini 红色物体追踪演示

此 demo 使用 Reachy Mini SDK 在机器人本体上运行，结合 OpenCV 视觉追踪：
- 使用 Reachy Mini 内置摄像头捕获图像
- 使用 OpenCV 检测红色螺丝刀
- 根据物体位置控制头部转动（yaw, pitch）
- 保持物体在视野中央

依赖:
- reachy_mini (Reachy Mini SDK)
- opencv-python (OpenCV)
- numpy

安全限制 (SDK 自动限制):
- Head Pitch: [-40°, +40°]
- Head Yaw: [-180°, +180°]

运行平台: Reachy Mini 机器人本体
"""

import time
import math
import numpy as np
import cv2
import threading
import queue
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose


class RedObjectTracker:
    """红色物体追踪器"""

    def __init__(self):
        """初始化追踪器"""
        # HSV 颜色范围 - 红色
        # 红色在 HSV 中有两个范围：[0, 10] 和 [170, 180]
        self.lower_red1 = np.array([0, 120, 70])
        self.upper_red1 = np.array([10, 255, 255])
        self.lower_red2 = np.array([170, 120, 70])
        self.upper_red2 = np.array([180, 255, 255])

        # 控制参数
        self.yaw_limit = 30      # 左右转动最大角度
        self.pitch_limit = 20    # 上下转动最大角度
        self.deadzone = 0.15     # 死区比例（中心区域不移动）
        self.gain = 0.8          # 控制增益（响应速度）

    def find_red_object(self, frame):
        """在图像中查找红色物体

        Args:
            frame: 输入图像（BGR 格式）

        Returns:
            (center_x, center_y, area): 物体中心坐标和面积，如果没找到返回 None
        """
        # 转换到 HSV 颜色空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 创建红色掩码（合并两个范围）
        mask1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        # 形态学操作，去除噪点
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # 找到最大的轮廓
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)

        # 过滤太小的区域
        if area < 500:
            return None

        # 计算中心点
        M = cv2.moments(largest_contour)
        if M["m00"] == 0:
            return None

        center_x = int(M["m10"] / M["m00"])
        center_y = int(M["m01"] / M["m00"])

        return (center_x, center_y, area)

    def calculate_head_angles(self, obj_x, obj_y, frame_width, frame_height):
        """根据物体位置计算头部转动角度

        Args:
            obj_x: 物体 X 坐标
            obj_y: 物体 Y 坐标
            frame_width: 图像宽度
            frame_height: 图像高度

        Returns:
            (yaw, pitch): 头部转动角度
        """
        # 计算物体相对于图像中心的偏移（归一化到 [-1, 1]）
        offset_x = (obj_x - frame_width / 2) / (frame_width / 2)
        offset_y = (obj_y - frame_height / 2) / (frame_height / 2)

        # 死区处理：在中心区域不移动
        if abs(offset_x) < self.deadzone:
            target_yaw = 0
        else:
            # 计算目标角度
            target_yaw = offset_x * self.yaw_limit * self.gain

        if abs(offset_y) < self.deadzone:
            target_pitch = 0
        else:
            # 计算目标角度（注意：向上看是负值，向下看是正值）
            target_pitch = offset_y * self.pitch_limit * self.gain

        # 限制角度范围
        target_yaw = max(-self.yaw_limit, min(self.yaw_limit, target_yaw))
        target_pitch = max(-self.pitch_limit, min(self.pitch_limit, target_pitch))

        return target_yaw, target_pitch

    def draw_debug_info(self, frame, obj_info, yaw, pitch):
        """在图像上绘制调试信息

        Args:
            frame: 输入图像
            obj_info: 物体信息 (x, y, area) 或 None
            yaw: 当前 yaw 角度
            pitch: 当前 pitch 角度
        """
        height, width = frame.shape[:2]

        # 绘制中心十字
        center_x = width // 2
        center_y = height // 2
        cv2.line(frame, (center_x - 50, center_y), (center_x + 50, center_y), (0, 255, 0), 2)
        cv2.line(frame, (center_x, center_y - 50), (center_x, center_y + 50), (0, 255, 0), 2)

        # 绘制死区
        deadzone_x = int(width * self.deadzone / 2)
        deadzone_y = int(height * self.deadzone / 2)
        cv2.rectangle(frame,
                     (center_x - deadzone_x, center_y - deadzone_y),
                     (center_x + deadzone_x, center_y + deadzone_y),
                     (255, 255, 0), 1)

        # 如果找到物体，绘制信息
        if obj_info:
            x, y, area = obj_info
            # 绘制物体中心
            cv2.circle(frame, (x, y), 10, (0, 0, 255), -1)
            # 绘制连线到中心
            cv2.line(frame, (x, y), (center_x, center_y), (0, 255, 0), 1)
            # 显示面积
            cv2.putText(frame, f"Area: {area}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 显示当前角度
        cv2.putText(frame, f"Yaw: {yaw:.1f}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Pitch: {pitch:.1f}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return frame


class DisplayThread:
    """独立的显示线程，避免 X11 线程问题"""

    def __init__(self, window_name="Red Object Tracking"):
        self.window_name = window_name
        self.frame_queue = queue.Queue(maxsize=2)
        self.running = False
        self.thread = None

    def start(self):
        """启动显示线程"""
        self.running = True
        self.thread = threading.Thread(target=self._display_loop, daemon=True)
        self.thread.start()

    def _display_loop(self):
        """显示循环（在独立线程中运行）"""
        # 在显示线程中初始化 OpenCV 窗口
        cv2.startWindowThread()
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 640, 480)

        while self.running:
            try:
                # 从队列获取帧（超时 100ms）
                frame = self.frame_queue.get(timeout=0.1)
                if frame is not None:
                    cv2.imshow(self.window_name, frame)
                self.frame_queue.task_done()

                # 检查退出键
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
            except queue.Empty:
                continue
            except Exception as e:
                print(f"显示错误: {e}")
                break

        # 清理
        cv2.destroyWindow(self.window_name)

    def update_frame(self, frame):
        """更新显示帧"""
        try:
            # 非阻塞方式放入队列，如果队列满则丢弃旧帧
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self.frame_queue.put_nowait(frame)
        except Exception as e:
            pass  # 静默处理显示错误

    def stop(self):
        """停止显示线程"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        cv2.destroyAllWindows()


def track_red_object(duration=60, show_preview=False):
    """追踪红色物体并控制头部

    Args:
        duration: 追踪时长（秒）
        show_preview: 是否显示预览窗口
    """
    print("=" * 60)
    print("🤖 Reachy Mini 红色物体追踪演示")
    print("=" * 60)
    print("\n📋 功能说明:")
    print("  - 使用 Reachy Mini 内置摄像头检测红色螺丝刀")
    print("  - 根据物体位置控制头部转动")
    print("  - 保持物体在视野中央")
    print("\n⚠️  请将红色螺丝刀放在摄像头前")
    print("=" * 60)

    # 初始化追踪器
    tracker = RedObjectTracker()

    # 初始化显示线程
    display_thread = None
    if show_preview:
        try:
            display_thread = DisplayThread("Red Object Tracking")
            display_thread.start()
            print("✅ 显示窗口已启动")
        except Exception as e:
            print(f"⚠️  无法启动显示窗口: {e}")
            print("   将继续运行但不显示预览")
            show_preview = False

    try:
        # 连接到 Reachy Mini（自动初始化摄像头）
        print("\n🔌 连接到 Reachy Mini...")
        with ReachyMini(media_backend="default") as mini:
            print("✅ 连接成功!")
            print(f"✅ 摄像头已打开")
            print(f"   分辨率: {mini.media.camera.resolution}")

            start_time = time.time()
            frame_count = 0
            fps = 0
            last_fps_time = start_time

            print(f"\n🎯 开始追踪（持续 {duration} 秒）...")
            if show_preview:
                print("   按 'q' 键退出")

            while display_thread is None or display_thread.running:
                # 检查时间
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    print(f"\n⏱️  追踪时间结束 ({duration} 秒)")
                    break

                # 从 Reachy Mini 获取摄像头帧
                frame = mini.media.get_frame()
                if frame is None:
                    print("❌ 无法读取摄像头")
                    break

                # 复制帧，因为从 SDK 获取的帧是只读的
                frame = frame.copy()

                frame_count += 1
                # 计算帧率
                if frame_count % 10 == 0:
                    current_time = time.time()
                    fps = 10 / (current_time - last_fps_time)
                    last_fps_time = current_time

                # 查找红色物体
                obj_info = tracker.find_red_object(frame)

                # 获取图像尺寸
                height, width = frame.shape[:2]

                # 计算头部角度
                if obj_info:
                    obj_x, obj_y, area = obj_info
                    yaw, pitch = tracker.calculate_head_angles(obj_x, obj_y, width, height)

                    # 控制头部
                    mini.goto_target(
                        head=create_head_pose(
                            yaw=yaw,
                            pitch=pitch
                        ),
                        duration=0.1,
                        method="minjerk"
                    )
                else:
                    # 没找到物体，保持当前位置（或慢慢回到中心）
                    yaw, pitch = 0, 0

                # 绘制调试信息
                frame = tracker.draw_debug_info(frame, obj_info, yaw, pitch)

                # 显示帧率
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, height - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                # 显示预览（通过显示线程）
                if show_preview and display_thread:
                    display_thread.update_frame(frame)

                # 控制循环速度
                time.sleep(0.05)

            print(f"\n{'='*60}")
            print("🎉 追踪完成!")
            print(f"   总帧数: {frame_count}")
            print(f"   平均帧率: {fps:.1f} FPS")
            print('='*60)

            # 回到正中
            print("\n🔄 回到正中...")
            mini.goto_target(
                head=create_head_pose(
                    yaw=0,
                    pitch=0
                ),
                duration=1.0,
                method="minjerk"
            )
            time.sleep(1.2)

            # 检查是否被用户中断
            if show_preview and display_thread and not display_thread.running:
                print("\n⚠️  用户退出")

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")

    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理显示线程
        if display_thread:
            display_thread.stop()

        # 清理 OpenCV 资源
        try:
            cv2.destroyAllWindows()
        except:
            pass

    print("\n" + "="*60)
    print("演示结束!")
    print("="*60)


if __name__ == "__main__":
    # 运行红色物体追踪
    # duration: 追踪时长（秒）
    # show_preview: 是否显示预览窗口（在机器人上默认关闭）
    track_red_object(duration=60, show_preview=False)
