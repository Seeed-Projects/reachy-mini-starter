"""
位置滤波器 - 用于平滑检测到的坐标波动
"""

from collections import deque


class PositionFilter:
    """位置滤波器 - 移动平均 + 跳变抑制"""

    def __init__(self, window_size=5, jump_threshold=30):
        """
        初始化位置滤波器

        Args:
            window_size: 滑动窗口大小，用于移动平均滤波
            jump_threshold: 跳变阈值（像素），超过此值的跳变会被抑制
        """
        self.window_size = window_size
        self.jump_threshold = jump_threshold

        # 历史位置队列
        self.x_history = deque(maxlen=window_size)
        self.y_history = deque(maxlen=window_size)

        # 上一次输出的位置
        self.last_output_x = None
        self.last_output_y = None

    def filter(self, x, y):
        """
        对输入坐标进行滤波

        Args:
            x, y: 原始坐标

        Returns:
            (filtered_x, filtered_y): 滤波后的坐标
        """
        # 如果是第一次输入，直接返回
        if self.last_output_x is None:
            self.x_history.append(x)
            self.y_history.append(y)
            self.last_output_x = x
            self.last_output_y = y
            return x, y

        # 检测跳变 - 如果与上一次输出差异过大，抑制跳变
        delta_x = abs(x - self.last_output_x)
        delta_y = abs(y - self.last_output_y)

        if delta_x > self.jump_threshold or delta_y > self.jump_threshold:
            # 检测到跳变，限制变化量
            limited_x = self.last_output_x + max(-self.jump_threshold // 2,
                                                   min(self.jump_threshold // 2, x - self.last_output_x))
            limited_y = self.last_output_y + max(-self.jump_threshold // 2,
                                                   min(self.jump_threshold // 2, y - self.last_output_y))
            self.x_history.append(limited_x)
            self.y_history.append(limited_y)
        else:
            # 正常情况，添加原始值
            self.x_history.append(x)
            self.y_history.append(y)

        # 计算移动平均值
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
        """重置滤波器状态"""
        self.x_history.clear()
        self.y_history.clear()
        self.last_output_x = None
        self.last_output_y = None
