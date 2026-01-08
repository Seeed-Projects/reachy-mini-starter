#!/usr/bin/env python3
"""
Demo 15: Reachy Mini 实时控制上位机 - WebSocket 中间件版本

Flask 服务器提供 WebSocket 接口，前端通过 WebSocket 连接到本服务器，
服务器再将命令转发到 Reachy Mini 的 REST API。

架构：
浏览器 ──[Socket.IO]──> Flask 服务器 ──[HTTP POST]──> 机器人 API
前端发送(度数)      后端转换为弧度              API需要(弧度)

⚠️ 重要单位转换说明：
- 前端显示/用户输入：度数 (degrees) - 用户友好
- 后端发送给 API：弧度 (radians) - API 要求
- 转换公式: radians = degrees × π / 180

API 参数单位（实测验证）：
| 参数 | 单位 | 范围 |
|------|------|------|
| head_pose.roll/pitch/yaw | 弧度 | roll/pitch: ±0.44, yaw: ±2.79 |
| antennas[] | 弧度 | ±1.40 |
| body_yaw | 弧度 | ±1.40 (实际约 ±0.88) |

参考：Demo 06 (06_zenoh_basic_control) 使用弧度值

依赖: pip install flask flask-socketio eventlet requests

运行: python server.py
然后在浏览器访问 http://localhost:5000
"""

import sys
import time
import requests
from pathlib import Path
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

# 添加上级目录到路径以导入配置模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config

# 加载配置
robot_config = get_config()

# Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'reachy-mini-websocket-control-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 机器人 API 基础 URL
ROBOT_API = robot_config.base_url


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect(data=None):
    """客户端连接"""
    print(f'客户端连接: {request.sid}')
    emit('connected', {'status': 'ok', 'robot_api': ROBOT_API})


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print(f'客户端断开: {request.sid}')


@socketio.on('move_command')
def handle_move_command(data):
    """
    接收来自前端的运动命令，转发到机器人 REST API

    Args:
        data: {
            'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'roll': 0.0,
            'pitch': 0.0,
            'yaw': 0.0,
            'antennas': [0.0, 0.0],
            'body_yaw': 0.0
        }
    """
    try:
        import math

        # 头部姿态欧拉角（度转弧度）
        roll_degrees = data.get('roll', 0.0)
        pitch_degrees = data.get('pitch', 0.0)
        yaw_degrees = data.get('yaw', 0.0)

        roll_radians = math.radians(roll_degrees)
        pitch_radians = math.radians(pitch_degrees)
        yaw_radians = math.radians(yaw_degrees)

        print(f"收到 head_pose: roll={roll_degrees}°, pitch={pitch_degrees}°, yaw={yaw_degrees}°")
        print(f"转换后 head_pose: roll={roll_radians:.3f}, pitch={pitch_radians:.3f}, yaw={yaw_radians:.3f} (弧度)")

        # 身体偏航（度转弧度）
        body_yaw_degrees = data.get('body_yaw', 0.0)
        body_yaw_radians = math.radians(body_yaw_degrees)
        print(f"收到 body_yaw: {body_yaw_degrees}° -> {body_yaw_radians:.3f} (弧度)")

        # 天线角度（度转弧度）
        antennas_degrees = data.get('antennas', [0, 0])
        antennas_radians = [math.radians(a) for a in antennas_degrees]
        print(f"收到 antennas: {antennas_degrees}° -> {[f'{a:.3f}' for a in antennas_radians]} (弧度)")

        # 使用 /move/goto 端点，它使用欧拉角格式，更容易处理
        payload = {
            'head_pose': {
                'x': data.get('position', {}).get('x', 0.0),
                'y': data.get('position', {}).get('y', 0.0),
                'z': data.get('position', {}).get('z', 0.0),
                'roll': roll_radians,
                'pitch': pitch_radians,
                'yaw': yaw_radians
            },
            'antennas': antennas_radians,
            'body_yaw': body_yaw_radians,
            'duration': 0.3,
            'interpolation': 'minjerk'
        }

        print(f"发送 payload 完成")

        response = requests.post(
            f"{ROBOT_API}/move/goto",
            json=payload,
            timeout=5
        )

        if response.status_code == 200:
            emit('move_result', {'success': True})
        else:
            emit('move_result', {'success': False, 'error': f'API 错误: {response.status_code} - {response.text}'})

    except Exception as e:
        emit('move_result', {'success': False, 'error': str(e)})


@socketio.on('enable_motors')
def handle_enable_motors():
    """启用电机"""
    try:
        response = requests.post(
            f"{ROBOT_API}/motors/set_mode/enabled",
            timeout=5
        )
        emit('motors_result', {
            'action': 'enable',
            'success': response.status_code == 200
        })
    except Exception as e:
        emit('motors_result', {
            'action': 'enable',
            'success': False,
            'error': str(e)
        })


@socketio.on('disable_motors')
def handle_disable_motors():
    """禁用电机"""
    try:
        response = requests.post(
            f"{ROBOT_API}/motors/set_mode/disabled",
            timeout=5
        )
        emit('motors_result', {
            'action': 'disable',
            'success': response.status_code == 200
        })
    except Exception as e:
        emit('motors_result', {
            'action': 'disable',
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    print("=" * 60)
    print("Demo 15: Reachy Mini 实时控制 (WebSocket 中间件)")
    print("=" * 60)
    print()
    print(f"机器人配置: {robot_config}")
    print(f"机器人 API: {ROBOT_API}")
    print()
    print("架构说明:")
    print("  浏览器 ──[WebSocket]──> Flask 服务器 ──[HTTP]──> 机器人 API")
    print(f"            :5000                         :8000")
    print()
    print("启动服务器...")
    print()

    # 获取本机 IP
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"

    print("=" * 60)
    print("服务器已启动!")
    print("=" * 60)
    print(f"本地访问: http://localhost:5000")
    print(f"局域网访问: http://{local_ip}:5000")
    print()
    print("在浏览器中打开上述地址即可开始控制")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()

    # 启动服务器
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
