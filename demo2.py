"""
Reachy Mini 滑块控制界面
通过 GUI 滑块实时控制机器人的头部、天线和身体姿态
"""

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import math

try:
    from tkinter import Tk, Scale, HORIZONTAL, VERTICAL, Label, Frame, Button, StringVar
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Warning: tkinter not available, running in console mode only")


class ReachyMiniController:
    """Reachy Mini 控制器 - 支持滑块控制"""

    def __init__(self):
        self.mini = ReachyMini()

        # 默认值（单位：度或毫米）
        self.head_defaults = {
            'x': 0,           # 前后位置 (mm), 范围: ±50
            'y': 0,           # 左右位置 (mm), 范围: ±50
            'z': 0,           # 上下位置 (mm), 范围: -30 ~ +80
            'roll': 0,        # 翻滚角 (度), 范围: ±25
            'pitch': 0,       # 俯仰角 (度), 范围: ±35
            'yaw': 0,         # 偏航角 (度), 范围: ±160
        }

        self.antenna_defaults = {
            'left': 0,        # 左天线 (度), 范围: -80 ~ +80
            'right': 0,       # 右天线 (度), 范围: -80 ~ +80
        }

        self.body_defaults = {
            'body_yaw': 0,    # 身体偏航角 (度), 范围: -160 ~ +160
        }

        # 当前值
        self.current_values = {
            **self.head_defaults,
            **self.antenna_defaults,
            **self.body_defaults
        }

        # 运动参数
        self.duration = 1.0

    def disconnect(self):
        """断开连接"""
        self.mini.client.disconnect()

    def send_move_command(self):
        """发送运动控制指令到机器人（带插值）"""
        try:
            head_pose = create_head_pose(
                x=self.current_values['x'],
                y=self.current_values['y'],
                z=self.current_values['z'],
                roll=self.current_values['roll'],
                pitch=self.current_values['pitch'],
                yaw=self.current_values['yaw'],
                degrees=True,
                mm=True
            )

            left_rad = math.radians(self.current_values['left'])
            right_rad = math.radians(self.current_values['right'])
            body_yaw_rad = math.radians(self.current_values['body_yaw'])

            self.mini.goto_target(
                head=head_pose,
                antennas=[left_rad, right_rad],
                duration=self.duration,
                body_yaw=body_yaw_rad,
            )
            print(f"Move sent: duration={self.duration}s")

        except Exception as e:
            print(f"Error in send_move_command: {e}")

    def set_target_command(self):
        """立即设置目标位置（实时响应，无插值）"""
        try:
            head_pose = create_head_pose(
                x=self.current_values['x'],
                y=self.current_values['y'],
                z=self.current_values['z'],
                roll=self.current_values['roll'],
                pitch=self.current_values['pitch'],
                yaw=self.current_values['yaw'],
                degrees=True,
                mm=True
            )

            left_rad = math.radians(self.current_values['left'])
            right_rad = math.radians(self.current_values['right'])
            body_yaw_rad = math.radians(self.current_values['body_yaw'])

            self.mini.set_target(
                head=head_pose,
                antennas=[left_rad, right_rad],
                body_yaw=body_yaw_rad,
            )

        except Exception as e:
            print(f"Error in set_target_command: {e}")

    def update_value(self, name, value):
        """更新单个控制值"""
        self.current_values[name] = value

    def reset_to_center(self):
        """重置到中心位置"""
        for key in self.head_defaults:
            self.current_values[key] = self.head_defaults[key]
        for key in self.antenna_defaults:
            self.current_values[key] = self.antenna_defaults[key]
        for key in self.body_defaults:
            self.current_values[key] = self.body_defaults[key]
        self.send_move_command()


class ReachyMiniGUI:
    """Reachy Mini GUI 控制界面"""

    def __init__(self, controller):
        self.controller = controller
        self.sliders = {}
        self.root = None

    def create_slider(self, parent, label, name, min_val, max_val, default):
        """创建滑块控件"""
        frame = Frame(parent)
        frame.pack(fill='x', padx=5, pady=2)

        # 标签和当前值显示
        label_frame = Frame(frame)
        label_frame.pack(fill='x')
        Label(label_frame, text=label, width=20, anchor='w').pack(side='left')
        value_var = StringVar(value=f"{default:.1f}")
        Label(label_frame, textvariable=value_var, width=8, anchor='e').pack(side='right')

        def on_change(val):
            value = float(val)
            value_var.set(f"{value:.1f}")
            self.controller.update_value(name, value)
            # 实时发送指令
            self.controller.set_target_command()

        scale = Scale(frame, from_=min_val, to=max_val, orient=HORIZONTAL,
                     command=on_change, resolution=0.1, length=300)
        scale.set(default)
        scale.pack()

        self.sliders[name] = scale
        return scale

    def build(self):
        """构建 GUI 界面"""
        self.root = Tk()
        self.root.title("Reachy Mini 控制面板")
        self.root.geometry("550x750")

        # 标题
        Label(self.root, text="Reachy Mini 运动控制", font=("Arial", 16, "bold")).pack(pady=10)

        # 头部位置控制
        head_pos_frame = Frame(self.root)
        head_pos_frame.pack(pady=5)
        Label(head_pos_frame, text="=== 头部位置 (毫米) ===", font=("Arial", 11, "bold")).pack()

        self.create_slider(head_pos_frame, "X (前后)", 'x', -50, 50, 0)
        self.create_slider(head_pos_frame, "Y (左右)", 'y', -50, 50, 0)
        self.create_slider(head_pos_frame, "Z (上下)", 'z', -30, 80, 0)

        # 头部角度控制
        head_angle_frame = Frame(self.root)
        head_angle_frame.pack(pady=5)
        Label(head_angle_frame, text="=== 头部角度 (度) ===", font=("Arial", 11, "bold")).pack()

        self.create_slider(head_angle_frame, "Roll (翻滚)", 'roll', -25, 25, 0)
        self.create_slider(head_angle_frame, "Pitch (俯仰)", 'pitch', -35, 35, 0)
        self.create_slider(head_angle_frame, "Yaw (偏航)", 'yaw', -160, 160, 0)

        # 天线控制
        antenna_frame = Frame(self.root)
        antenna_frame.pack(pady=5)
        Label(antenna_frame, text="=== 天线角度 (度) ===", font=("Arial", 11, "bold")).pack()

        self.create_slider(antenna_frame, "左天线", 'left', -80, 80, 0)
        self.create_slider(antenna_frame, "右天线", 'right', -80, 80, 0)

        # 身体控制
        body_frame = Frame(self.root)
        body_frame.pack(pady=5)
        Label(body_frame, text="=== 身体角度 (度) ===", font=("Arial", 11, "bold")).pack()

        self.create_slider(body_frame, "Body Yaw", 'body_yaw', -160, 160, 0)

        # 运动参数
        param_frame = Frame(self.root)
        param_frame.pack(pady=10)
        Label(param_frame, text="=== 运动参数 ===", font=("Arial", 11, "bold")).pack()

        # Duration 滑块 (单独处理，不触发实时更新)
        dur_frame = Frame(param_frame)
        dur_frame.pack(fill='x', padx=5, pady=2)
        dur_label_frame = Frame(dur_frame)
        dur_label_frame.pack(fill='x')
        Label(dur_label_frame, text="Duration (秒)", width=20, anchor='w').pack(side='left')
        dur_var = StringVar(value="1.0")
        Label(dur_label_frame, textvariable=dur_var, width=8, anchor='e').pack(side='right')

        def on_duration_change(val):
            self.controller.duration = float(val)
            dur_var.set(f"{float(val):.1f}")

        duration_scale = Scale(dur_frame, from_=0.1, to=10.0, orient=HORIZONTAL,
                              command=on_duration_change, resolution=0.1, length=300)
        duration_scale.set(1.0)
        duration_scale.pack()

        # 按钮区域
        btn_frame = Frame(self.root)
        btn_frame.pack(pady=15)

        Button(btn_frame, text="重置到中心位置", command=self.reset,
               bg="#4CAF50", fg="white", font=("Arial", 11), padx=20, pady=8).pack(side='left', padx=5)

        Button(btn_frame, text="退出", command=self.quit,
               bg="#f44336", fg="white", font=("Arial", 11), padx=20, pady=8).pack(side='left', padx=5)

    def reset(self):
        """重置所有滑块"""
        self.controller.reset_to_center()
        # 更新所有滑块位置
        for name, slider in self.sliders.items():
            default = self.controller.current_values[name]
            slider.set(default)

    def quit(self):
        """退出程序"""
        self.controller.disconnect()
        if self.root:
            self.root.destroy()

    def run(self):
        """运行 GUI"""
        self.build()
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.mainloop()


def main():
    """主函数"""
    print("正在初始化 Reachy Mini 控制器...")

    controller = ReachyMiniController()

    if GUI_AVAILABLE:
        print("启动 GUI 控制界面...")
        gui = ReachyMiniGUI(controller)
        gui.run()
    else:
        print("GUI 不可用，请安装 tkinter")
        controller.disconnect()


if __name__ == "__main__":
    main()
