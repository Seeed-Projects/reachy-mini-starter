#!/usr/bin/env python3
"""
Demo 13: 网页版遥控摄像头 - 后端服务器

通过浏览器控制 Reachy Mini 机器人头部摄像头，实现局域网内的远程监控。
使用 Flask + WebSocket 提供实时视频流和头部运动控制。

依赖: pip install flask flask-socketio eventlet requests

运行: python server.py
然后在浏览器访问 http://localhost:5000 (或 http://<本机IP>:5000)
"""

import sys
import json
import time
import requests
from pathlib import Path
from threading import Thread
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

# 添加上级目录到路径以导入配置模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_loader import get_config

# 加载配置
robot_config = get_config()

# Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'reachy-mini-remote-camera-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 机器人 API 基础 URL
ROBOT_API = robot_config.base_url

# 全局状态
robot_state = {
    'connected': False,
    'head_pose': {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 0, 'yaw': 0},
    'video_url': None
}


def check_robot_connection():
    """检查机器人连接状态"""
    try:
        response = requests.get(f"{ROBOT_API}/motors/status", timeout=2)
        robot_state['connected'] = response.status_code == 200
    except:
        robot_state['connected'] = False
    return robot_state['connected']


def get_video_stream_url():
    """获取视频流 URL"""
    # 使用机器人的 IP 和信令端口
    return f"http://{robot_config.robot_ip}:8443"


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html',
                         robot_ip=robot_config.robot_ip,
                         robot_port=robot_config.robot_port)


@app.route('/api/status')
def api_status():
    """API 状态端点"""
    return jsonify({
        'connected': robot_state['connected'],
        'robot_ip': robot_config.robot_ip,
        'head_pose': robot_state['head_pose']
    })


@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f'客户端连接: {request.sid}')
    emit('status', {
        'connected': robot_state['connected'],
        'robot_ip': robot_config.robot_ip,
        'video_url': get_video_stream_url()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    print(f'客户端断开: {request.sid}')


@socketio.on('check_connection')
def handle_check_connection():
    """检查机器人连接"""
    connected = check_robot_connection()
    emit('connection_status', {'connected': connected})


@socketio.on('move_head')
def handle_move_head(data):
    """
    处理头部运动控制

    参数:
        data: {
            'axis': 'x'|'y'|'z'|'roll'|'pitch'|'yaw',
            'value': number (角度或位置值),
            'duration': number (可选，运动时长，秒)
        }
    """
    try:
        axis = data.get('axis')
        value = data.get('value')
        duration = data.get('duration', 0.5)

        # 更新当前姿态
        robot_state['head_pose'][axis] = value

        # 发送运动命令到机器人
        payload = {
            'head_pose': robot_state['head_pose'].copy(),
            'duration': duration,
            'interpolation': 'minjerk'
        }

        response = requests.post(
            f"{ROBOT_API}/move/goto",
            json=payload,
            timeout=5
        )

        if response.status_code == 200:
            emit('move_result', {'success': True, 'axis': axis, 'value': value})
        else:
            emit('move_result', {'success': False, 'error': f'API 错误: {response.status_code}'})

    except Exception as e:
        emit('move_result', {'success': False, 'error': str(e)})


@socketio.on('reset_head')
def handle_reset_head():
    """重置头部到中心位置"""
    try:
        reset_pose = {'x': 0, 'y': 0, 'z': 0, 'roll': 0, 'pitch': 0, 'yaw': 0}
        robot_state['head_pose'] = reset_pose.copy()

        payload = {
            'head_pose': reset_pose,
            'duration': 1.0,
            'interpolation': 'minjerk'
        }

        response = requests.post(
            f"{ROBOT_API}/move/goto",
            json=payload,
            timeout=5
        )

        emit('reset_result', {'success': response.status_code == 200})

    except Exception as e:
        emit('reset_result', {'success': False, 'error': str(e)})


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
    """禁用电机（可手动移动）"""
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


def background_check_connection():
    """后台线程：定期检查机器人连接"""
    while True:
        check_robot_connection()
        socketio.sleep(5)  # 每 5 秒检查一次


if __name__ == '__main__':
    print("=" * 60)
    print("Demo 13: 网页版遥控摄像头 - 后端服务器")
    print("=" * 60)
    print()
    print(f"机器人配置: {robot_config}")
    print(f"机器人 API: {ROBOT_API}")
    print()
    print("启动服务器...")
    print()

    # 启动后台检查线程
    socketio.start_background_task(background_check_connection)

    # 获取本机 IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

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
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
