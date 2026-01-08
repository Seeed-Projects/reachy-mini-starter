// 全局状态
let socket = null;
let currentPose = {
    x: 0,
    y: 0,
    z: 0,
    roll: 0,
    pitch: 0,
    yaw: 0
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initSocket();
    log('系统初始化完成', 'info');
});

// 初始化 WebSocket 连接
function initSocket() {
    socket = io();

    socket.on('connect', function() {
        log('已连接到服务器', 'success');
        updateConnectionStatus('connected');
        socket.emit('check_connection');
    });

    socket.on('disconnect', function() {
        log('与服务器的连接已断开', 'error');
        updateConnectionStatus('disconnected');
    });

    socket.on('status', function(data) {
        log('服务器状态: ' + (data.connected ? '已连接机器人' : '未连接机器人'), 'info');
        updateConnectionStatus(data.connected ? 'connected' : 'disconnected');
    });

    socket.on('connection_status', function(data) {
        const status = data.connected ? '已连接' : '未连接';
        log('机器人连接状态: ' + status, data.connected ? 'success' : 'warning');
        updateConnectionStatus(data.connected ? 'connected' : 'disconnected');
    });

    socket.on('move_result', function(data) {
        if (data.success) {
            log(`头部运动: ${data.axis} = ${data.value}`, 'success');
        } else {
            log('运动失败: ' + data.error, 'error');
        }
    });

    socket.on('reset_result', function(data) {
        if (data.success) {
            log('头部位置已重置', 'success');
            resetSliders();
        } else {
            log('重置失败: ' + data.error, 'error');
        }
    });

    socket.on('motors_result', function(data) {
        const action = data.action === 'enable' ? '启用' : '禁用';
        if (data.success) {
            log(`电机已${action}`, 'success');
        } else {
            log(`电机${action}失败: ` + data.error, 'error');
        }
    });
}

// 更新连接状态显示
function updateConnectionStatus(status) {
    const dot = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');

    dot.className = 'status-dot ' + status;

    switch(status) {
        case 'connected':
            text.textContent = '已连接';
            break;
        case 'disconnected':
            text.textContent = '未连接';
            break;
        default:
            text.textContent = '连接中...';
    }
}

// 更新轴位置
function updateAxis(axis, value) {
    value = parseFloat(value);
    currentPose[axis] = value;

    // 更新显示值
    const valueDisplay = document.getElementById(axis + 'Value');
    if (valueDisplay) {
        if (axis === 'z') {
            valueDisplay.textContent = (value / 100).toFixed(2) + 'm';
        } else {
            valueDisplay.textContent = value + '°';
        }
    }

    // 发送运动命令
    socket.emit('move_head', {
        axis: axis,
        value: value,
        duration: 0.5
    });
}

// 重置头部位置
function resetHead() {
    log('重置头部位置...', 'info');
    socket.emit('reset_head');
}

// 重置滑块
function resetSliders() {
    document.getElementById('yawSlider').value = 0;
    document.getElementById('pitchSlider').value = 0;
    document.getElementById('rollSlider').value = 0;
    document.getElementById('zSlider').value = 0;

    document.getElementById('yawValue').textContent = '0°';
    document.getElementById('pitchValue').textContent = '0°';
    document.getElementById('rollValue').textContent = '0°';
    document.getElementById('zValue').textContent = '0m';

    currentPose = {
        x: 0,
        y: 0,
        z: 0,
        roll: 0,
        pitch: 0,
        yaw: 0
    };
}

// 启用电机
function enableMotors() {
    log('启用电机...', 'info');
    socket.emit('enable_motors');
}

// 禁用电机
function disableMotors() {
    log('禁用电机...', 'info');
    socket.emit('disable_motors');
}

// 设置预设位置
function setPreset(preset) {
    const presets = {
        forward: { yaw: 0, pitch: 0, roll: 0 },
        left: { yaw: -45, pitch: 0, roll: 0 },
        right: { yaw: 45, pitch: 0, roll: 0 },
        up: { yaw: 0, pitch: 25, roll: 0 },
        down: { yaw: 0, pitch: -25, roll: 0 }
    };

    const pose = presets[preset];
    if (pose) {
        log(`设置预设位置: ${preset}`, 'info');

        // 更新滑块
        document.getElementById('yawSlider').value = pose.yaw;
        document.getElementById('pitchSlider').value = pose.pitch;
        document.getElementById('rollSlider').value = pose.roll;

        // 更新显示
        document.getElementById('yawValue').textContent = pose.yaw + '°';
        document.getElementById('pitchValue').textContent = pose.pitch + '°';
        document.getElementById('rollValue').textContent = pose.roll + '°';

        // 更新当前姿态
        currentPose.yaw = pose.yaw;
        currentPose.pitch = pose.pitch;
        currentPose.roll = pose.roll;

        // 发送运动命令
        socket.emit('move_head', {
            axis: 'yaw',
            value: pose.yaw,
            duration: 1.0
        });

        setTimeout(() => {
            socket.emit('move_head', {
                axis: 'pitch',
                value: pose.pitch,
                duration: 1.0
            });
        }, 100);

        setTimeout(() => {
            socket.emit('move_head', {
                axis: 'roll',
                value: pose.roll,
                duration: 1.0
            });
        }, 200);
    }
}

// 添加日志
function log(message, type = 'info') {
    const container = document.getElementById('logContainer');
    const entry = document.createElement('div');
    entry.className = 'log-entry ' + type;

    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;

    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;

    // 限制日志条数
    while (container.children.length > 50) {
        container.removeChild(container.firstChild);
    }
}

// 打开视频播放器
function openVideoPlayer() {
    document.getElementById('videoModal').classList.add('show');
}

// 关闭视频播放器
function closeVideoPlayer() {
    document.getElementById('videoModal').classList.remove('show');
}

// 显示视频帮助
function showVideoHelp() {
    alert('视频流说明:\n\n' +
          '1. 确保机器人已开启视频流服务\n' +
          '2. 在终端运行: python3 demos/05_webrtc_video_stream/05.py --signaling-host ' +
          document.getElementById('robotIp').textContent +
          '\n\n' +
          '详细说明请查看"打开视频播放器"按钮。');
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('videoModal');
    if (event.target === modal) {
        closeVideoPlayer();
    }
}

// 键盘快捷键
document.addEventListener('keydown', function(event) {
    // 如果焦点在滑块上，不处理快捷键
    if (event.target.tagName === 'INPUT') {
        return;
    }

    const step = 5;
    let handled = false;

    switch(event.key) {
        case 'ArrowLeft':
            updateAxis('yaw', Math.max(-160, currentPose.yaw - step));
            document.getElementById('yawSlider').value = currentPose.yaw;
            handled = true;
            break;
        case 'ArrowRight':
            updateAxis('yaw', Math.min(160, currentPose.yaw + step));
            document.getElementById('yawSlider').value = currentPose.yaw;
            handled = true;
            break;
        case 'ArrowUp':
            updateAxis('pitch', Math.min(35, currentPose.pitch + step));
            document.getElementById('pitchSlider').value = currentPose.pitch;
            handled = true;
            break;
        case 'ArrowDown':
            updateAxis('pitch', Math.max(-35, currentPose.pitch - step));
            document.getElementById('pitchSlider').value = currentPose.pitch;
            handled = true;
            break;
        case 'r':
        case 'R':
            resetHead();
            handled = true;
            break;
    }

    if (handled) {
        event.preventDefault();
    }
});
