/**
 * Demo 17: Reachy Mini 控制模块
 * 基于 Demo 15 的 WebSocket 控制逻辑
 */

class RobotControl {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.debounceTimers = new Map();

        // DOM 元素缓存
        this.elements = {
            wsStatusDot: document.getElementById('wsStatusDot'),
            wsStatusText: document.getElementById('wsStatusText'),
            updateRate: document.getElementById('updateRate'),
            enableMotors: document.getElementById('enableMotors'),
            disableMotors: document.getElementById('disableMotors'),
            resetAll: document.getElementById('resetAll')
        };

        // 所有滑块配置
        this.sliders = [
            { id: 'headX', valueId: 'headXValue', format: v => parseFloat(v).toFixed(3) },
            { id: 'headY', valueId: 'headYValue', format: v => parseFloat(v).toFixed(3) },
            { id: 'headZ', valueId: 'headZValue', format: v => parseFloat(v).toFixed(3) },
            { id: 'headRoll', valueId: 'headRollValue', format: v => v + '°' },
            { id: 'headPitch', valueId: 'headPitchValue', format: v => v + '°' },
            { id: 'headYaw', valueId: 'headYawValue', format: v => v + '°' },
            { id: 'antennaLeft', valueId: 'antennaLeftValue', format: v => v + '°' },
            { id: 'antennaRight', valueId: 'antennaRightValue', format: v => v + '°' },
            { id: 'bodyYaw', valueId: 'bodyYawValue', format: v => v + '°' }
        ];

        this.init();
    }

    init() {
        this.connectSocket();
        this.setupSliders();
        this.setupButtons();
        this.setupSettings();
    }

    /**
     * 连接 WebSocket
     */
    connectSocket() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000
            });

            this.socket.on('connect', () => this.onConnect());
            this.socket.on('disconnect', () => this.onDisconnect());
            this.socket.on('connected', (data) => this.onServerConnected(data));
            this.socket.on('move_result', (data) => this.onMoveResult(data));
            this.socket.on('motors_result', (data) => this.onMotorsResult(data));

        } catch (error) {
            console.error('Socket.IO 初始化失败:', error);
            this.updateConnectionStatus(false);
        }
    }

    /**
     * 连接成功
     */
    onConnect() {
        this.isConnected = true;
        this.updateConnectionStatus(true);
        console.log('WebSocket 已连接');
        this.showToast('控制器已连接', false);
    }

    /**
     * 断开连接
     */
    onDisconnect() {
        this.isConnected = false;
        this.updateConnectionStatus(false);
        console.log('WebSocket 已断开');
        this.showToast('控制器已断开', true);
    }

    /**
     * 服务器确认连接
     */
    onServerConnected(data) {
        console.log('服务器确认连接:', data);
    }

    /**
     * 运动命令结果
     */
    onMoveResult(data) {
        if (!data.success) {
            console.error('运动命令失败:', data.error);
        }
    }

    /**
     * 电机操作结果
     */
    onMotorsResult(data) {
        if (data.success) {
            const message = data.action === 'enable' ? '电机已启用' : '电机已禁用';
            this.showToast(message, false);
        } else {
            this.showToast('操作失败: ' + (data.error || '未知错误'), true);
        }
    }

    /**
     * 更新连接状态显示
     */
    updateConnectionStatus(connected) {
        if (this.elements.wsStatusDot) {
            this.elements.wsStatusDot.classList.toggle('connected', connected);
        }
        if (this.elements.wsStatusText) {
            this.elements.wsStatusText.textContent = connected ? '已连接' : '未连接';
        }
    }

    /**
     * 设置滑块事件
     */
    setupSliders() {
        this.sliders.forEach(config => {
            const slider = document.getElementById(config.id);
            const valueDisplay = document.getElementById(config.valueId);

            if (!slider || !valueDisplay) return;

            slider.addEventListener('input', (e) => {
                // 更新显示值
                valueDisplay.textContent = config.format(e.target.value);

                // 防抖发送命令
                const sliderId = config.id;
                if (this.debounceTimers.has(sliderId)) {
                    clearTimeout(this.debounceTimers.get(sliderId));
                }

                this.debounceTimers.set(sliderId, setTimeout(() => {
                    this.sendMoveCommand();
                }, 20)); // 20ms 防抖
            });
        });
    }

    /**
     * 设置按钮事件
     */
    setupButtons() {
        if (this.elements.enableMotors) {
            this.elements.enableMotors.addEventListener('click', () => {
                this.socket.emit('enable_motors');
            });
        }

        if (this.elements.disableMotors) {
            this.elements.disableMotors.addEventListener('click', () => {
                this.socket.emit('disable_motors');
            });
        }

        if (this.elements.resetAll) {
            this.elements.resetAll.addEventListener('click', () => this.resetAll());
        }
    }

    /**
     * 设置控制选项
     */
    setupSettings() {
        if (this.elements.updateRate) {
            this.elements.updateRate.addEventListener('change', () => {
                this.showToast('更新频率已更新', false);
            });
        }
    }

    /**
     * 发送运动命令
     */
    sendMoveCommand() {
        if (!this.isConnected) return;

        const command = {
            position: {
                x: parseFloat(document.getElementById('headX').value),
                y: parseFloat(document.getElementById('headY').value),
                z: parseFloat(document.getElementById('headZ').value)
            },
            roll: parseFloat(document.getElementById('headRoll').value),
            pitch: parseFloat(document.getElementById('headPitch').value),
            yaw: parseFloat(document.getElementById('headYaw').value),
            antennas: [
                parseFloat(document.getElementById('antennaLeft').value),
                parseFloat(document.getElementById('antennaRight').value)
            ],
            body_yaw: parseFloat(document.getElementById('bodyYaw').value)
        };

        this.socket.emit('move_command', command);
    }

    /**
     * 全部回零
     */
    resetAll() {
        this.sliders.forEach(config => {
            const slider = document.getElementById(config.id);
            const valueDisplay = document.getElementById(config.valueId);

            if (slider && valueDisplay) {
                slider.value = 0;
                valueDisplay.textContent = config.format(0);
            }
        });

        this.sendMoveCommand();
        this.showToast('已全部回零', false);
    }

    /**
     * 显示提示消息
     */
    showToast(message, isError = false) {
        const toast = document.getElementById('toast');
        if (!toast) return;

        toast.textContent = message;
        toast.className = 'toast show' + (isError ? ' error' : '');

        setTimeout(() => {
            toast.className = 'toast';
        }, 2500);
    }
}

// 导出到全局
window.RobotControl = RobotControl;
