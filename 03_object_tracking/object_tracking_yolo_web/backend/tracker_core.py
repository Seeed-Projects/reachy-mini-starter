"""
Core tracking logic - Shared between original and web versions
"""

import math
from collections import deque
from threading import Lock


class PositionFilter:
    """位置滤波器 - 移动平均 + 跳变抑制"""

    def __init__(self, window_size=5, jump_threshold=30):
        self.window_size = window_size
        self.jump_threshold = jump_threshold
        self.x_history = deque(maxlen=window_size)
        self.y_history = deque(maxlen=window_size)
        self.last_output_x = None
        self.last_output_y = None

    def filter(self, x, y):
        if self.last_output_x is None:
            self.x_history.append(x)
            self.y_history.append(y)
            self.last_output_x = x
            self.last_output_y = y
            return x, y

        delta_x = abs(x - self.last_output_x)
        delta_y = abs(y - self.last_output_y)

        if delta_x > self.jump_threshold or delta_y > self.jump_threshold:
            limited_x = self.last_output_x + max(-self.jump_threshold // 2,
                                                   min(self.jump_threshold // 2, x - self.last_output_x))
            limited_y = self.last_output_y + max(-self.jump_threshold // 2,
                                                   min(self.jump_threshold // 2, y - self.last_output_y))
            self.x_history.append(limited_x)
            self.y_history.append(limited_y)
        else:
            self.x_history.append(x)
            self.y_history.append(y)

        if len(self.x_history) > 0:
            filtered_x = sum(self.x_history) / len(self.x_history)
            filtered_y = sum(self.y_history) / len(self.y_history)
        else:
            filtered_x = x
            filtered_y = y

        self.last_output_x = filtered_x
        self.last_output_y = filtered_y

        return filtered_x, filtered_y

    def reset(self):
        self.x_history.clear()
        self.y_history.clear()
        self.last_output_x = None
        self.last_output_y = None


class HeadPitchController:
    """头部 Pitch 控制器 - PID 控制"""

    def __init__(self, pid_p=0.5, pid_i=0.0, pid_d=0.0, pitch_limit=35, dead_zone=0.05):
        self.pid_p = pid_p
        self.pid_i = pid_i
        self.pid_d = pid_d
        self.gain = 0.08
        self.pitch_limit = math.radians(pitch_limit)
        self.dead_zone = dead_zone
        self.current_pitch = 0.0
        self.integral = 0.0
        self.last_error = 0.0

    def normalize_to_center(self, y, frame_height):
        center_y = frame_height / 2
        norm_y = (y - center_y) / center_y
        return norm_y

    def compute(self, target_y, frame_height, dt):
        error = self.normalize_to_center(target_y, frame_height)

        if abs(error) < self.dead_zone:
            return self.current_pitch

        p = self.pid_p * error
        self.integral += error * dt
        self.integral = max(-1.0, min(1.0, self.integral))
        i = self.pid_i * self.integral

        d = 0.0
        if dt > 0:
            d = self.pid_d * (error - self.last_error) / dt
        self.last_error = error

        control = p + i + d
        control = max(-1.0, min(1.0, control))

        pitch_adjustment = control * self.gain
        new_pitch = self.current_pitch + pitch_adjustment
        new_pitch = max(-self.pitch_limit, min(self.pitch_limit, new_pitch))

        return new_pitch

    def update(self, new_pitch):
        self.current_pitch = new_pitch

    def reset(self):
        self.current_pitch = 0.0
        self.integral = 0.0
        self.last_error = 0.0


class HeadYawController:
    """头部 Yaw 控制器 - PID 控制"""

    def __init__(self, pid_p=0.5, pid_i=0.0, pid_d=0.0, yaw_limit=160, dead_zone=0.05):
        self.pid_p = pid_p
        self.pid_i = pid_i
        self.pid_d = pid_d
        self.gain = 0.08
        self.yaw_limit = math.radians(yaw_limit)
        self.dead_zone = dead_zone
        self.current_yaw = 0.0
        self.integral = 0.0
        self.last_error = 0.0

    def normalize_to_center(self, x, frame_width):
        center_x = frame_width / 2
        norm_x = (x - center_x) / center_x
        return norm_x

    def compute(self, target_x, frame_width, dt):
        error = self.normalize_to_center(target_x, frame_width)

        if abs(error) < self.dead_zone:
            return self.current_yaw

        p = self.pid_p * error
        self.integral += error * dt
        self.integral = max(-1.0, min(1.0, self.integral))
        i = self.pid_i * self.integral

        d = 0.0
        if dt > 0:
            d = self.pid_d * (error - self.last_error) / dt
        self.last_error = error

        control = p + i + d
        control = max(-1.0, min(1.0, control))

        yaw_adjustment = -control * self.gain
        new_yaw = self.current_yaw + yaw_adjustment
        new_yaw = max(-self.yaw_limit, min(self.yaw_limit, new_yaw))

        return new_yaw

    def update(self, new_yaw):
        self.current_yaw = new_yaw

    def reset(self):
        self.current_yaw = 0.0
        self.integral = 0.0
        self.last_error = 0.0
