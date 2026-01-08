"""
头部 Yaw 控制器 - 使用头部旋转进行水平追踪
"""

import math


class HeadYawController:
    """头部 Yaw 控制器 - PID 控制"""

    def __init__(self, pid_p=0.5, pid_i=0.0, pid_d=0.0, yaw_limit=160, dead_zone=0.05):
        """
        初始化控制器

        Args:
            pid_p: 比例系数
            pid_i: 积分系数
            pid_d: 微分系数
            yaw_limit: Yaw 角度限制（度）
            dead_zone: 死区比例（目标在中央此范围内时不调整）
        """
        self.pid_p = pid_p
        self.pid_i = pid_i
        self.pid_d = pid_d
        self.gain = 0.08  # 增益系数，可通过滑条动态调整
        self.yaw_limit = math.radians(yaw_limit)
        self.dead_zone = dead_zone

        # 当前状态
        self.current_yaw = 0.0

        # PID 状态
        self.integral = 0.0
        self.last_error = 0.0

    def normalize_to_center(self, x, frame_width):
        """
        将图像 x 坐标归一化到中心坐标系

        Args:
            x: 图像 x 坐标
            frame_width: 帧宽度

        Returns:
            norm_x: 归一化坐标，范围 [-1, 1]，0 表示中心
        """
        center_x = frame_width / 2
        norm_x = (x - center_x) / center_x
        return norm_x

    def compute(self, target_x, frame_width, dt):
        """
        计算控制输出

        Args:
            target_x: 目标 x 坐标
            frame_width: 帧宽度
            dt: 时间步长

        Returns:
            new_yaw: 新的头部 Yaw 角度（弧度）
        """
        # 归一化误差
        error = self.normalize_to_center(target_x, frame_width)

        # 检查死区
        if abs(error) < self.dead_zone:
            return self.current_yaw

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

        # 计算新的头部 Yaw 角度
        # 图像坐标系：x 向右增大（从左到右）
        # 目标在右侧（x > center, error > 0）→ 头部需要向右转 → 需要**负** Yaw
        # 目标在左侧（x < center, error < 0）→ 头部需要向左转 → 需要**正** Yaw
        yaw_adjustment = -control * self.gain  # 使用动态增益
        new_yaw = self.current_yaw + yaw_adjustment

        # 限制范围
        new_yaw = max(-self.yaw_limit, min(self.yaw_limit, new_yaw))

        return new_yaw

    def update(self, new_yaw):
        """更新当前 Yaw 状态"""
        self.current_yaw = new_yaw

    def reset(self):
        """重置控制器状态"""
        self.current_yaw = 0.0
        self.integral = 0.0
        self.last_error = 0.0
