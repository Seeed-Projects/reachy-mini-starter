// YOLO 目标追踪 - 前端应用

class TrackingApp {
    constructor() {
        this.apiBase = 'http://localhost:8123';
        this.infoUpdateInterval = 100;
        this.infoTimer = null;
        this.currentAxis = 'pitch';
        this.availableClasses = [];
        this.canvas = null;
        this.ctx = null;

        this.init();
    }

    async init() {
        // 设置 Canvas
        this.setupCanvas();

        // 设置视频流状态
        this.setupVideoStatus();

        // 等待后端就绪
        await this.waitForBackend();

        // 加载可用类别
        await this.loadClasses();

        // 加载当前参数
        await this.loadParams();

        // 设置事件监听器
        this.setupEventListeners();

        // 开始信息更新
        this.startInfoUpdates();

        // 显示通知
        this.showNotification('应用加载成功', 'success');
    }

    setupCanvas() {
        this.canvas = document.getElementById('overlayCanvas');
        this.ctx = this.canvas.getContext('2d');

        // 设置 canvas 尺寸匹配视频
        const videoImg = document.getElementById('videoStream');
        videoImg.onload = () => {
            this.resizeCanvas();
        };

        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        const videoWrapper = document.querySelector('.video-wrapper');
        if (videoWrapper && this.canvas) {
            this.canvas.width = videoWrapper.offsetWidth;
            this.canvas.height = videoWrapper.offsetHeight;
        }
    }

    setupVideoStatus() {
        const videoImg = document.getElementById('videoStream');

        videoImg.onload = () => {
            const statusText = document.getElementById('statusText');
            const statusIndicator = document.getElementById('statusIndicator');
            statusText.textContent = '直播中';
            statusIndicator.classList.add('live');
        };

        videoImg.onerror = () => {
            const statusText = document.getElementById('statusText');
            statusText.textContent = '连接错误';
        };
    }

    async waitForBackend() {
        let attempts = 0;
        const maxAttempts = 50;

        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`${this.apiBase}/api/health`);
                const data = await response.json();

                if (data.status === 'ready') {
                    console.log('后端就绪!');
                    return;
                }

                console.log(`后端初始化中... (${attempts + 1}/${maxAttempts})`);
            } catch (error) {
                console.log('等待后端...', error);
            }

            attempts++;
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        console.warn('后端初始化超时，继续执行');
    }

    setupEventListeners() {
        // 控制按钮
        document.getElementById('startBtn').addEventListener('click', () => this.startTracking());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopTracking());
        document.getElementById('resetBtn').addEventListener('click', () => this.resetTracking());

        // 检测器设置
        document.getElementById('classSelect').addEventListener('change', (e) => {
            this.updateDetectorSettings(e.target.value);
        });

        document.getElementById('confThreshold').addEventListener('input', (e) => {
            document.getElementById('confThresholdValue').textContent = e.target.value;
        });
        document.getElementById('confThreshold').addEventListener('change', (e) => {
            this.updateDetectorSettings(null, parseFloat(e.target.value));
        });

        // 滤波器设置
        document.getElementById('filterWindowSize').addEventListener('input', (e) => {
            document.getElementById('filterWindowSizeValue').textContent = e.target.value;
        });
        document.getElementById('filterWindowSize').addEventListener('change', (e) => {
            this.updateFilterSettings(parseInt(e.target.value), null);
        });

        document.getElementById('filterJumpThreshold').addEventListener('input', (e) => {
            document.getElementById('filterJumpThresholdValue').textContent = e.target.value;
        });
        document.getElementById('filterJumpThreshold').addEventListener('change', (e) => {
            this.updateFilterSettings(null, parseInt(e.target.value));
        });

        // 轴切换
        document.getElementById('pitchTab').addEventListener('click', () => this.switchAxis('pitch'));
        document.getElementById('yawTab').addEventListener('click', () => this.switchAxis('yaw'));

        // Pitch 滑块
        this.setupSlider('pitchP', 'pitchPValue', 'p', 'pitch');
        this.setupSlider('pitchI', 'pitchIValue', 'i', 'pitch');
        this.setupSlider('pitchD', 'pitchDValue', 'd', 'pitch');
        this.setupSlider('pitchGain', 'pitchGainValue', 'gain', 'pitch');

        // Yaw 滑块
        this.setupSlider('yawP', 'yawPValue', 'p', 'yaw');
        this.setupSlider('yawI', 'yawIValue', 'i', 'yaw');
        this.setupSlider('yawD', 'yawDValue', 'd', 'yaw');
        this.setupSlider('yawGain', 'yawGainValue', 'gain', 'yaw');
    }

    setupSlider(sliderId, valueId, param, axis) {
        const slider = document.getElementById(sliderId);
        const valueDisplay = document.getElementById(valueId);

        slider.addEventListener('input', (e) => {
            valueDisplay.textContent = e.target.value;
        });

        slider.addEventListener('change', (e) => {
            const value = parseFloat(e.target.value);
            if (axis === 'pitch') {
                this.updatePitchParams(param, value);
            } else {
                this.updateYawParams(param, value);
            }
        });
    }

    switchAxis(axis) {
        this.currentAxis = axis;

        // 更新标签页样式
        document.getElementById('pitchTab').classList.toggle('active', axis === 'pitch');
        document.getElementById('yawTab').classList.toggle('active', axis === 'yaw');

        // 更新内容可见性
        document.getElementById('pitchContent').classList.toggle('active', axis === 'pitch');
        document.getElementById('yawContent').classList.toggle('active', axis === 'yaw');
    }

    async loadClasses() {
        try {
            const response = await fetch(`${this.apiBase}/api/classes`);
            const data = await response.json();
            this.availableClasses = data.classes || [];

            const select = document.getElementById('classSelect');
            select.innerHTML = '';
            this.availableClasses.forEach(cls => {
                const option = document.createElement('option');
                option.value = cls;
                option.textContent = cls.charAt(0).toUpperCase() + cls.slice(1);
                select.appendChild(option);
            });

            select.value = 'bottle';
        } catch (error) {
            console.error('加载类别失败:', error);
        }
    }

    async loadParams() {
        try {
            const response = await fetch(`${this.apiBase}/api/params`);
            const data = await response.json();

            // 更新 Pitch 参数
            if (data.pitch) {
                document.getElementById('pitchP').value = data.pitch.p;
                document.getElementById('pitchPValue').textContent = data.pitch.p;
                document.getElementById('pitchI').value = data.pitch.i;
                document.getElementById('pitchIValue').textContent = data.pitch.i;
                document.getElementById('pitchD').value = data.pitch.d;
                document.getElementById('pitchDValue').textContent = data.pitch.d;
                document.getElementById('pitchGain').value = data.pitch.gain;
                document.getElementById('pitchGainValue').textContent = data.pitch.gain;
            }

            // 更新 Yaw 参数
            if (data.yaw) {
                document.getElementById('yawP').value = data.yaw.p;
                document.getElementById('yawPValue').textContent = data.yaw.p;
                document.getElementById('yawI').value = data.yaw.i;
                document.getElementById('yawIValue').textContent = data.yaw.i;
                document.getElementById('yawD').value = data.yaw.d;
                document.getElementById('yawDValue').textContent = data.yaw.d;
                document.getElementById('yawGain').value = data.yaw.gain;
                document.getElementById('yawGainValue').textContent = data.yaw.gain;
            }

            // 更新检测器设置
            if (data.detector) {
                document.getElementById('classSelect').value = data.detector.target_class || 'bottle';
                document.getElementById('confThreshold').value = data.detector.conf_threshold || 0.3;
                document.getElementById('confThresholdValue').textContent = data.detector.conf_threshold || 0.3;
            }

            // 更新滤波器设置
            if (data.filter) {
                document.getElementById('filterWindowSize').value = data.filter.window_size || 5;
                document.getElementById('filterWindowSizeValue').textContent = data.filter.window_size || 5;
                document.getElementById('filterJumpThreshold').value = data.filter.jump_threshold || 30;
                document.getElementById('filterJumpThresholdValue').textContent = data.filter.jump_threshold || 30;
            }
        } catch (error) {
            console.error('加载参数失败:', error);
        }
    }

    async startTracking() {
        try {
            const response = await fetch(`${this.apiBase}/api/control/start`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                this.showNotification('追踪已启动', 'success');
                this.updateControlButtons(true);
            } else {
                this.showNotification(data.message, 'error');
            }
        } catch (error) {
            console.error('启动追踪失败:', error);
            this.showNotification('启动追踪失败', 'error');
        }
    }

    async stopTracking() {
        try {
            const response = await fetch(`${this.apiBase}/api/control/stop`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                this.showNotification('追踪已停止', 'success');
                this.updateControlButtons(false);
            }
        } catch (error) {
            console.error('停止追踪失败:', error);
            this.showNotification('停止追踪失败', 'error');
        }
    }

    async resetTracking() {
        try {
            const response = await fetch(`${this.apiBase}/api/control/reset`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                this.showNotification('状态已重置', 'success');
            }
        } catch (error) {
            console.error('重置失败:', error);
            this.showNotification('重置失败', 'error');
        }
    }

    updateControlButtons(isRunning) {
        document.getElementById('startBtn').disabled = isRunning;
        document.getElementById('stopBtn').disabled = !isRunning;
    }

    async updatePitchParams(param, value) {
        try {
            const params = {};
            params[param] = value;

            const response = await fetch(`${this.apiBase}/api/params/pitch`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });

            const data = await response.json();
            if (data.success) {
                console.log(`Pitch ${param} 更新为 ${value}`);
            }
        } catch (error) {
            console.error('更新 Pitch 参数失败:', error);
        }
    }

    async updateYawParams(param, value) {
        try {
            const params = {};
            params[param] = value;

            const response = await fetch(`${this.apiBase}/api/params/yaw`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });

            const data = await response.json();
            if (data.success) {
                console.log(`Yaw ${param} 更新为 ${value}`);
            }
        } catch (error) {
            console.error('更新 Yaw 参数失败:', error);
        }
    }

    async updateDetectorSettings(targetClass, confThreshold) {
        try {
            const settings = {};

            if (targetClass !== null) {
                settings.target_class = targetClass;
            }
            if (confThreshold !== null) {
                settings.conf_threshold = confThreshold;
            }

            const response = await fetch(`${this.apiBase}/api/params/detector`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('检测器设置已更新', 'success');
            }
        } catch (error) {
            console.error('更新检测器设置失败:', error);
            this.showNotification('更新检测器设置失败', 'error');
        }
    }

    async updateFilterSettings(windowSize, jumpThreshold) {
        try {
            const settings = {};

            if (windowSize !== null) {
                settings.window_size = windowSize;
            }
            if (jumpThreshold !== null) {
                settings.jump_threshold = jumpThreshold;
            }

            const response = await fetch(`${this.apiBase}/api/params/filter`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('滤波器设置已更新', 'success');
            }
        } catch (error) {
            console.error('更新滤波器设置失败:', error);
            this.showNotification('更新滤波器设置失败', 'error');
        }
    }

    startInfoUpdates() {
        this.infoTimer = setInterval(() => {
            this.updateInfo();
        }, this.infoUpdateInterval);
    }

    async updateInfo() {
        try {
            const response = await fetch(`${this.apiBase}/api/info`);
            const info = await response.json();

            // 更新状态
            if (info.is_running) {
                document.getElementById('trackingStatus').textContent = '追踪中';
                document.getElementById('trackingStatus').style.color = 'var(--success)';
            } else {
                document.getElementById('trackingStatus').textContent = '未追踪';
                document.getElementById('trackingStatus').style.color = 'var(--danger)';
            }

            // 更新角度
            if (info.pitch !== undefined) {
                const pitchDeg = (info.pitch * 180 / Math.PI).toFixed(1);
                document.getElementById('pitchAngle').textContent = `${pitchDeg}°`;
            }

            if (info.yaw !== undefined) {
                const yawDeg = (info.yaw * 180 / Math.PI).toFixed(1);
                document.getElementById('yawAngle').textContent = `${yawDeg}°`;
            }

            // 更新目标类别
            if (info.target_class) {
                document.getElementById('targetClass').textContent =
                    info.target_class.charAt(0).toUpperCase() + info.target_class.slice(1);
            }

            // 更新检测数
            if (info.detection_count !== undefined) {
                document.getElementById('detectionCount').textContent = info.detection_count;
            }

            // 更新控制按钮状态
            this.updateControlButtons(info.is_running);

            // 绘制检测结果到 Canvas
            this.drawDetection(info);

        } catch (error) {
            console.error('更新信息失败:', error);
        }
    }

    drawDetection(info) {
        if (!this.ctx || !this.canvas) return;

        const displayWidth = this.canvas.width;
        const displayHeight = this.canvas.height;

        // 清空 canvas
        this.ctx.clearRect(0, 0, displayWidth, displayHeight);

        // 原始摄像头分辨率（与后端一致）
        const sourceWidth = 1280;
        const sourceHeight = 960;

        // 计算缩放比例
        const scaleX = displayWidth / sourceWidth;
        const scaleY = displayHeight / sourceHeight;

        // 由于 object-fit: cover，需要考虑裁剪
        const sourceAspectRatio = sourceWidth / sourceHeight;
        const displayAspectRatio = displayWidth / displayHeight;

        let renderWidth, renderHeight, offsetX, offsetY;

        if (sourceAspectRatio > displayAspectRatio) {
            renderHeight = displayHeight;
            renderWidth = displayHeight * sourceAspectRatio;
            offsetX = (displayWidth - renderWidth) / 2;
            offsetY = 0;
        } else {
            renderWidth = displayWidth;
            renderHeight = displayWidth / sourceAspectRatio;
            offsetX = 0;
            offsetY = (displayHeight - renderHeight) / 2;
        }

        // 坐标转换函数
        const toDisplayCoord = (x, y) => {
            return {
                x: x * (renderWidth / sourceWidth) + offsetX,
                y: y * (renderHeight / sourceHeight) + offsetY
            };
        };

        // 绘制中心十字准星 - 更精致的设计
        const center = toDisplayCoord(sourceWidth / 2, sourceHeight / 2);

        // 绘制渐变光晕效果
        const gradient = this.ctx.createRadialGradient(center.x, center.y, 0, center.x, center.y, 60);
        gradient.addColorStop(0, 'rgba(0, 255, 255, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 255, 255, 0)');
        this.ctx.fillStyle = gradient;
        this.ctx.beginPath();
        this.ctx.arc(center.x, center.y, 60, 0, Math.PI * 2);
        this.ctx.fill();

        // 绘制十字准星 - 带发光效果
        this.ctx.strokeStyle = '#00FFFF';
        this.ctx.lineWidth = 2;
        this.ctx.shadowColor = '#00FFFF';
        this.ctx.shadowBlur = 10;
        this.ctx.beginPath();
        this.ctx.moveTo(center.x - 25, center.y);
        this.ctx.lineTo(center.x + 25, center.y);
        this.ctx.moveTo(center.x, center.y - 25);
        this.ctx.lineTo(center.x, center.y + 25);
        this.ctx.stroke();
        this.ctx.shadowBlur = 0;

        // 绘制死区圆圈 - 虚线设计
        const deadZoneRadius = Math.min(renderWidth, renderHeight) * 0.05;
        this.ctx.strokeStyle = 'rgba(0, 255, 128, 0.6)';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.beginPath();
        this.ctx.arc(center.x, center.y, deadZoneRadius, 0, Math.PI * 2);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // 如果有检测结果，绘制检测框和相关信息
        if (info.is_tracking && info.detection_box && info.target_center) {
            const [x1, y1, x2, y2] = info.detection_box;
            const [targetX, targetY] = info.target_center;
            const [filteredX, filteredY] = info.filtered_center || [targetX, targetY];

            // 转换坐标
            const box1 = toDisplayCoord(x1, y1);
            const box2 = toDisplayCoord(x2, y2);
            const targetPos = toDisplayCoord(targetX, targetY);
            const filteredPos = toDisplayCoord(filteredX, filteredY);

            // 绘制检测框 - 圆角矩形 + 渐变边框
            const cornerRadius = 8;
            const boxWidth = box2.x - box1.x;
            const boxHeight = box2.y - box1.y;

            // 绘制外发光效果
            this.ctx.strokeStyle = 'rgba(0, 255, 128, 0.3)';
            this.ctx.lineWidth = 8;
            this.ctx.lineJoin = 'round';
            this.ctx.strokeRect(box1.x, box1.y, boxWidth, boxHeight);

            // 绘制主边框
            this.ctx.strokeStyle = '#00FF80';
            this.ctx.lineWidth = 2;
            this.ctx.shadowColor = '#00FF80';
            this.ctx.shadowBlur = 15;
            this.ctx.strokeRect(box1.x, box1.y, boxWidth, boxHeight);
            this.ctx.shadowBlur = 0;

            // 绘制角标装饰
            const cornerSize = 15;
            const cornerLineWidth = 3;
            this.ctx.strokeStyle = '#00FFFF';
            this.ctx.lineWidth = cornerLineWidth;
            this.ctx.lineCap = 'round';

            // 左上角
            this.ctx.beginPath();
            this.ctx.moveTo(box1.x - 5, box1.y + cornerSize);
            this.ctx.lineTo(box1.x - 5, box1.y - 5);
            this.ctx.lineTo(box1.x + cornerSize, box1.y - 5);
            this.ctx.stroke();

            // 右上角
            this.ctx.beginPath();
            this.ctx.moveTo(box2.x - cornerSize, box1.y - 5);
            this.ctx.lineTo(box2.x + 5, box1.y - 5);
            this.ctx.lineTo(box2.x + 5, box1.y + cornerSize);
            this.ctx.stroke();

            // 右下角
            this.ctx.beginPath();
            this.ctx.moveTo(box2.x + 5, box2.y - cornerSize);
            this.ctx.lineTo(box2.x + 5, box2.y + 5);
            this.ctx.lineTo(box2.x - cornerSize, box2.y + 5);
            this.ctx.stroke();

            // 左下角
            this.ctx.beginPath();
            this.ctx.moveTo(box1.x + cornerSize, box2.y + 5);
            this.ctx.lineTo(box1.x - 5, box2.y + 5);
            this.ctx.lineTo(box1.x - 5, box2.y - cornerSize);
            this.ctx.stroke();

            // 绘制原始检测中心 - 脉冲动画效果
            const pulseSize = 5 + Math.sin(Date.now() / 100) * 2;
            this.ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            this.ctx.shadowColor = '#FFFFFF';
            this.ctx.shadowBlur = 10;
            this.ctx.beginPath();
            this.ctx.arc(targetPos.x, targetPos.y, pulseSize, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.shadowBlur = 0;

            // 绘制滤波后中心 - 靶心设计
            this.ctx.fillStyle = 'rgba(0, 255, 128, 0.9)';
            this.ctx.shadowColor = '#00FF80';
            this.ctx.shadowBlur = 20;
            this.ctx.beginPath();
            this.ctx.arc(filteredPos.x, filteredPos.y, 12, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.shadowBlur = 0;

            // 绘制靶心环
            this.ctx.strokeStyle = '#FFFFFF';
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.arc(filteredPos.x, filteredPos.y, 8, 0, Math.PI * 2);
            this.ctx.stroke();

            // 绘制从滤波中心到图像中心的连线 - 渐变线条
            const lineGradient = this.ctx.createLinearGradient(filteredPos.x, filteredPos.y, center.x, center.y);
            lineGradient.addColorStop(0, 'rgba(0, 255, 128, 0.8)');
            lineGradient.addColorStop(1, 'rgba(0, 255, 255, 0.3)');
            this.ctx.strokeStyle = lineGradient;
            this.ctx.lineWidth = 3;
            this.ctx.shadowColor = '#00FF80';
            this.ctx.shadowBlur = 5;
            this.ctx.beginPath();
            this.ctx.moveTo(filteredPos.x, filteredPos.y);
            this.ctx.lineTo(center.x, center.y);
            this.ctx.stroke();
            this.ctx.shadowBlur = 0;

            // 绘制标签 - 背景卡片设计
            const labelText = `${info.target_class}: ${(info.confidence || 0).toFixed(2)}`;
            this.ctx.font = 'bold 13px "Segoe UI", Arial, sans-serif';
            const textWidth = this.ctx.measureText(labelText).width;
            const padding = 8;
            const labelHeight = 24;

            // 标签背景 - 渐变
            const labelGradient = this.ctx.createLinearGradient(box1.x, box1.y - 35, box1.x, box1.y - 35 + labelHeight);
            labelGradient.addColorStop(0, 'rgba(0, 0, 0, 0.8)');
            labelGradient.addColorStop(1, 'rgba(0, 50, 0, 0.8)');
            this.ctx.fillStyle = labelGradient;
            this.ctx.fillRect(box1.x - 2, box1.y - 35, textWidth + padding * 2, labelHeight);

            // 标签边框
            this.ctx.strokeStyle = '#00FF80';
            this.ctx.lineWidth = 1;
            this.ctx.strokeRect(box1.x - 2, box1.y - 35, textWidth + padding * 2, labelHeight);

            // 标签文字
            this.ctx.fillStyle = '#00FF80';
            this.ctx.fillText(labelText, box1.x + padding, box1.y - 18);

            // 绘制坐标信息 - 现代信息卡片
            const infoBoxWidth = 140;
            const infoBoxHeight = 50;
            const infoBoxX = box1.x;
            const infoBoxY = box2.y + 10;

            // 信息卡片背景
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.75)';
            this.ctx.strokeStyle = 'rgba(0, 255, 128, 0.5)';
            this.ctx.lineWidth = 1;
            this.ctx.beginPath();
            this.ctx.roundRect(infoBoxX, infoBoxY, infoBoxWidth, infoBoxHeight, 6);
            this.ctx.fill();
            this.ctx.stroke();

            // 坐标信息文字
            this.ctx.font = '11px "Segoe UI", Arial, sans-serif';
            this.ctx.fillStyle = '#CCCCCC';
            this.ctx.fillText(`位置: (${Math.round(targetPos.x)}, ${Math.round(targetPos.y)})`, infoBoxX + 8, infoBoxY + 18);

            const offsetXPx = Math.round(filteredPos.x - center.x);
            const offsetYPx = Math.round(filteredPos.y - center.y);
            this.ctx.fillStyle = offsetXPx === 0 && offsetYPx === 0 ? '#00FF80' : '#FFAA00';
            this.ctx.fillText(`偏移: (${offsetXPx}, ${offsetYPx})`, infoBoxX + 8, infoBoxY + 38);
        }

        // 绘制状态指示器 - 左上角胶囊设计
        const statusY = 20;
        const status = info.is_running ? "追踪中" : "未追踪";
        const statusColor = info.is_running ? '#00FF80' : '#FF4444';
        const statusBgColor = info.is_running ? 'rgba(0, 255, 128, 0.2)' : 'rgba(255, 68, 68, 0.2)';

        // 状态背景
        const statusWidth = 100;
        const statusHeight = 28;
        this.ctx.fillStyle = statusBgColor;
        this.ctx.strokeStyle = statusColor;
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.roundRect(20, statusY, statusWidth, statusHeight, 14);
        this.ctx.fill();
        this.ctx.stroke();

        // 状态指示灯
        this.ctx.fillStyle = statusColor;
        this.ctx.shadowColor = statusColor;
        this.ctx.shadowBlur = 10;
        this.ctx.beginPath();
        this.ctx.arc(32, statusY + 14, 5, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.shadowBlur = 0;

        // 状态文字
        this.ctx.font = 'bold 13px "Segoe UI", Arial, sans-serif';
        this.ctx.fillStyle = statusColor;
        this.ctx.fillText(status, 45, statusY + 19);

        // 绘制目标类别 - 胶囊设计
        if (info.target_class) {
            const targetY = statusY + 38;
            const targetText = `目标: ${info.target_class.charAt(0).toUpperCase() + info.target_class.slice(1)}`;

            this.ctx.fillStyle = 'rgba(0, 100, 255, 0.2)';
            this.ctx.strokeStyle = '#4488FF';
            this.ctx.lineWidth = 1;
            this.ctx.beginPath();
            this.ctx.roundRect(20, targetY, 140, 24, 12);
            this.ctx.fill();
            this.ctx.stroke();

            this.ctx.font = '12px "Segoe UI", Arial, sans-serif';
            this.ctx.fillStyle = '#4488FF';
            this.ctx.fillText(targetText, 30, targetY + 17);
        }

        // 绘制当前角度 - 现代数据展示
        if (info.pitch !== undefined && info.yaw !== undefined) {
            const pitchDeg = (info.pitch * 180 / Math.PI).toFixed(1);
            const yawDeg = (info.yaw * 180 / Math.PI).toFixed(1);

            const angleY = displayHeight - 50;
            const angleBoxWidth = 240;
            const angleBoxHeight = 60;

            // 角度信息卡片背景
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.strokeStyle = 'rgba(255, 200, 0, 0.5)';
            this.ctx.lineWidth = 1;
            this.ctx.beginPath();
            this.ctx.roundRect(20, angleY, angleBoxWidth, angleBoxHeight, 8);
            this.ctx.fill();
            this.ctx.stroke();

            // Pitch 角度
            this.ctx.font = 'bold 12px "Segoe UI", Arial, sans-serif';
            this.ctx.fillStyle = '#AAAAAA';
            this.ctx.fillText('PITCH (俯仰)', 35, angleY + 20);
            this.ctx.font = 'bold 18px "Segoe UI", Arial, sans-serif';
            this.ctx.fillStyle = '#FFCC00';
            this.ctx.fillText(`${pitchDeg}°`, 140, angleY + 20);

            // Yaw 角度
            this.ctx.font = 'bold 12px "Segoe UI", Arial, sans-serif';
            this.ctx.fillStyle = '#AAAAAA';
            this.ctx.fillText('YAW (偏航)', 35, angleY + 45);
            this.ctx.font = 'bold 18px "Segoe UI", Arial, sans-serif';
            this.ctx.fillStyle = '#FFCC00';
            this.ctx.fillText(`${yawDeg}°`, 140, angleY + 45);
        }
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// DOM 加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.trackingApp = new TrackingApp();
});
