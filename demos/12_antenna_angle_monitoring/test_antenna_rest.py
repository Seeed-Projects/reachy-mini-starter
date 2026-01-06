#!/usr/bin/env python3
"""
Demo 12.1: 使用 REST API 查询天线舵机角度

通过 REST API 单次查询获取天线舵机的实时角度。
适用于：单次状态查询、低频监控场景。

依赖: pip install requests
"""

import requests
import time
import sys
from pathlib import Path
from datetime import datetime

# 添加上级目录到路径以导入配置模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config

# 加载配置
config = get_config()
# 使用 config.base_url，它已经包含了正确的 /api 前缀
BASE_URL = config.base_url


def rad_to_deg(radians):
    """将弧度转换为角度"""
    return radians * 180.0 / 3.14159265359


def get_antenna_angles():
    """
    通过 REST API 获取天线当前角度

    Returns:
        dict: 包含左右天线角度（弧度和度数）的字典
        None: 请求失败时返回 None
    """
    try:
        # 方式1: 使用专用接口获取天线角度
        response = requests.get(f"{BASE_URL}/state/present_antenna_joint_positions", timeout=5)

        if response.status_code == 200:
            angles_rad = response.json()  # 返回格式: [左天线弧度, 右天线弧度]

            return {
                "left_rad": angles_rad[0],
                "right_rad": angles_rad[1],
                "left_deg": rad_to_deg(angles_rad[0]),
                "right_deg": rad_to_deg(angles_rad[1])
            }
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
        return None


def get_antenna_angles_full():
    """
    通过完整状态接口获取天线角度（备用方式）

    Returns:
        dict: 包含完整状态中天线角度的字典
        None: 请求失败时返回 None
    """
    try:
        response = requests.get(f"{BASE_URL}/state/full", timeout=5)

        if response.status_code == 200:
            state = response.json()

            if "antennas_position" in state:
                angles_rad = state["antennas_position"]

                return {
                    "left_rad": angles_rad[0],
                    "right_rad": angles_rad[1],
                    "left_deg": rad_to_deg(angles_rad[0]),
                    "right_deg": rad_to_deg(angles_rad[1]),
                    "full_state": state  # 包含完整状态用于调试
                }
            else:
                print("完整状态中未找到天线位置数据")
                return None
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
        return None


def print_antenna_state(angles):
    """格式化打印天线状态"""
    if angles is None:
        print("无法获取天线状态")
        return

    print("\n" + "=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    print("天线舵机实时角度:")
    print("-" * 60)
    print(f"  左天线: {angles['left_rad']:7.3f} 弧度  ({angles['left_deg']:7.2f}°)")
    print(f"  右天线: {angles['right_rad']:7.3f} 弧度  ({angles['right_deg']:7.2f}°)")
    print("=" * 60 + "\n")


def monitor_antenna_angles(interval=1.0, duration=30):
    """
    持续监控天线角度

    Args:
        interval: 查询间隔（秒）
        duration: 总监控时长（秒），None 表示无限期
    """
    print(f"开始监控天线角度，间隔 {interval} 秒")
    print(f"监控时长: {duration} 秒（Ctrl+C 提前退出）")
    print("提示: 您可以手动移动天线，观察角度变化\n")

    start_time = time.time()
    query_count = 0

    try:
        while True:
            query_count += 1

            # 获取天线角度
            angles = get_antenna_angles()

            # 如果专用接口失败，尝试完整状态接口
            if angles is None:
                print("专用接口失败，尝试完整状态接口...")
                angles = get_antenna_angles_full()

            # 打印结果
            if angles:
                print_antenna_state(angles)
            else:
                print(f"[查询 #{query_count}] 获取失败")

            # 检查是否达到时长
            if duration and (time.time() - start_time) >= duration:
                break

            # 等待下次查询
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n监控已停止")

    print(f"\n总计查询次数: {query_count}")
    print(f"平均频率: {query_count / (time.time() - start_time):.2f} 次/秒")


def main():
    """主函数"""
    print("=" * 60)
    print("Demo 12.1: REST API 天线角度查询")
    print("=" * 60)
    print()
    print(f"机器人配置: {config}")
    print(f"API 地址: {BASE_URL}")
    print()

    # 先进行单次查询测试
    print("【测试 1】单次查询")
    angles = get_antenna_angles()
    print_antenna_state(angles)

    # 询问是否开始持续监控
    print("\n是否开始持续监控？")
    print("  - 输入监控间隔秒数（默认 1 秒）")
    print("  - 输入 'q' 退出")

    user_input = input("\n请选择: ").strip()

    if user_input.lower() == 'q':
        print("退出")
        return

    # 解析间隔时间
    try:
        interval = float(user_input) if user_input else 1.0
    except ValueError:
        interval = 1.0

    # 开始监控
    monitor_antenna_angles(interval=interval, duration=None)


if __name__ == "__main__":
    main()
