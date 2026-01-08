#!/usr/bin/env python3
"""接收 Reachy Mini 麦克风流并在本地播放（带命令行可视化）

运行方式:
    python3 receive_mic_stream.py

依赖:
    pip install websocket-client numpy
    sudo apt install ffmpeg  # Linux
    brew install ffmpeg      # macOS
"""

import websocket
import subprocess
import time
import sys
import shutil

# 机器人 IP 和端口
ROBOT_IP = "10.42.0.75"
PORT = "8002"

# 统计变量
bytes_received = 0
start_time = None
audio_level = 0  # 音频电平
last_display_time = 0


def calculate_audio_level(data):
    """计算音频电平"""
    global audio_level

    # 将字节数据转换为 numpy 数组（Opus 是编码后的，这里做简单估算）
    try:
        import numpy as np
        # 数据越大说明音频信号越强
        arr = np.frombuffer(data, dtype=np.uint8)
        if len(arr) > 0:
            # 计算信号强度（简化版）
            level = np.std(arr.astype(np.float32)) / 128.0
            audio_level = min(level, 1.0)
            # 慢速衰减
            audio_level = audio_level * 0.9 + 0.05
    except:
        audio_level = max(0, audio_level - 0.01)


def show_progress_bar(audio_level, kb, rate):
    """显示动态音频可视化"""
    # 获取终端宽度
    terminal_width = shutil.get_terminal_size().columns
    bar_width = min(50, terminal_width - 40)

    # 根据音频电平显示不同颜色和符号
    if audio_level > 0.3:
        bar_char = '█'
        status = '🎙️ 大'
    elif audio_level > 0.1:
        bar_char = '▓'
        status = '🎙️ 中'
    elif audio_level > 0.01:
        bar_char = '░'
        status = '🎙️ 小'
    else:
        bar_char = '·'
        status = '🔇 静音'

    # 计算进度条长度
    filled = int(audio_level * bar_width)
    bar = bar_char * filled + '·' * (bar_width - filled)

    # 显示信息
    info = f"{status} |{bar}| {audio_level:.2f} | {kb:.1f} KB ({rate:.1f} KB/s)"
    print(info, end='\r', flush=True)


def on_open(ws):
    global start_time
    start_time = time.time()
    print("✅ 已连接到机器人麦克风，正在监听...")
    print("提示: 按 Ctrl+C 停止接收\n")


def on_message(ws, message):
    global bytes_received, last_display_time

    if isinstance(message, bytes):
        # 写入 ffplay
        try:
            player.stdin.write(message)
            player.stdin.flush()
        except:
            pass

        # 统计
        bytes_received += len(message)
        calculate_audio_level(message)

        # 每 50ms 更新一次显示（避免闪烁）
        current_time = time.time()
        if current_time - last_display_time >= 0.05:
            elapsed = current_time - start_time
            kb = bytes_received / 1024
            rate = kb / elapsed if elapsed > 0 else 0
            show_progress_bar(audio_level, kb, rate)
            last_display_time = current_time


def on_error(ws, error):
    print(f"\n❌ 错误: {error}")


def on_close(ws, close_status_code, close_msg):
    global bytes_received, start_time
    print("\n### 已关闭连接 ###")
    if start_time:
        elapsed = time.time() - start_time
        kb = bytes_received / 1024
        print(f"总共接收: {kb:.1f} KB，耗时 {elapsed:.1f} 秒")


# 使用 ffplay 解码并播放
player = subprocess.Popen(
    ["ffplay", "-nodisp", "-loglevel", "quiet", "-"],
    stdin=subprocess.PIPE
)

# WebSocket 连接
ws = websocket.WebSocketApp(
    f"ws://{ROBOT_IP}:{PORT}/audio/mic",
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)
ws.on_open = on_open

print(f"连接到 {ROBOT_IP}:{PORT}/audio/mic")
print("启动中...")

ws.run_forever()
