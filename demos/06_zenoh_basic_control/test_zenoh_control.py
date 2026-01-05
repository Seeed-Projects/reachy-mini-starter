#!/usr/bin/env python3
"""Reachy Mini Zenoh 基础控制

使用 Zenoh 协议控制 Reachy Mini 机器人的运动和电机状态。
"""

import zenoh
import json
import time
import sys
from pathlib import Path

# 添加上级目录到路径以导入配置模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config


def main():
    """主函数 - 演示 Zenoh 控制功能"""
    # 从配置文件读取机器人 IP
    config = get_config()
    robot_ip = config.robot_ip
    robot_port = "7447"  # Zenoh 默认端口

    # Zenoh 话题定义
    topic_command = "reachy_mini/command"

    print("=" * 50)
    print("Reachy Mini Zenoh 控制")
    print("=" * 50)
    print(f"\n配置信息:")
    print(f"  机器人 IP: {robot_ip}")
    print(f"  Zenoh 端口: {robot_port}")
    print(f"  命令话题: {topic_command}")

    # 1. 配置 Zenoh 连接
    print(f"\n正在连接到机器人: tcp/{robot_ip}:{robot_port} ...")
    conf = zenoh.Config()

    # 强制指定连接端点 (点对点直连，不需要广播发现)
    conf.insert_json5("connect/endpoints", f"['tcp/{robot_ip}:{robot_port}']")

    try:
        session = zenoh.open(conf)
        print("✅ Zenoh Session 建立成功！")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n请确保:")
        print("  1. Reachy Mini 已开机")
        print("  2. 网络连接正常")
        print("  3. 已安装 zenoh-python: pip install zenoh")
        return

    # 2. 声明发布者 (Publisher)
    pub = session.declare_publisher(topic_command)
    print(f"📢 已建立指令通道: {topic_command}")

    try:
        # --- 步骤 A: 开启电机 (必须！) ---
        print("\n>>> [1/5] 发送指令: 开启电机 (Torque ON)")
        cmd_torque = {"torque": True, "ids": None}
        pub.put(json.dumps(cmd_torque))
        time.sleep(1.5)  # 给电机一点时间上劲

        # --- 步骤 B: 移动天线 ---
        print(">>> [2/5] 发送指令: 移动天线 (左歪)")
        # 左 30度 (约0.5弧度), 右 -30度
        cmd_antennas = {"antennas_joint_positions": [0.5, -0.5]}
        pub.put(json.dumps(cmd_antennas))
        time.sleep(1.0)

        print(">>> [2/5] 发送指令: 移动天线 (右歪)")
        cmd_antennas = {"antennas_joint_positions": [-0.5, 0.5]}
        pub.put(json.dumps(cmd_antennas))
        time.sleep(1.0)

        # --- 步骤 C: 旋转身体 ---
        print(">>> [3/5] 发送指令: 旋转身体 (左转)")
        cmd_body = {"body_yaw": 0.5}  # 转约 30度
        pub.put(json.dumps(cmd_body))
        time.sleep(1.0)

        print(">>> [3/5] 发送指令: 旋转身体 (回正)")
        cmd_body = {"body_yaw": 0.0}  # 回正
        pub.put(json.dumps(cmd_body))
        time.sleep(1.0)

        # --- 步骤 D: 点头动作 ---
        print(">>> [4/5] 发送指令: 点头")
        cmd_head = {"head_pose": {"pitch": -0.15}}
        pub.put(json.dumps(cmd_head))
        time.sleep(0.5)

        cmd_head = {"head_pose": {"pitch": 0.0}}
        pub.put(json.dumps(cmd_head))
        time.sleep(0.5)

        # --- 步骤 E: 归位 ---
        print(">>> [5/5] 发送指令: 全部归零")
        reset_cmd = {
            "antennas_joint_positions": [0.0, 0.0],
            "body_yaw": 0.0,
            "head_pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}
        }
        pub.put(json.dumps(reset_cmd))
        time.sleep(1.0)

        print("\n" + "=" * 50)
        print("完成!")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n操作已中断")
    finally:
        # 放松电机
        print(">>> 放松电机")
        cmd_relax = {"torque": False, "ids": None}
        pub.put(json.dumps(cmd_relax))
        session.close()
        print("🔌 连接已断开")


if __name__ == "__main__":
    main()
