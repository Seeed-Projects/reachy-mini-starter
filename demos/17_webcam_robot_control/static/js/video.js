/**
 * Demo 17: 视频流处理模块
 * 基于 Demo 18 的 MJPEG 视频流处理
 */

class VideoStream {
    constructor() {
        // DOM 元素
        this.elements = {
            videoFeed: document.getElementById('videoFeed'),
            videoStatusDot: document.getElementById('videoStatusDot'),
            videoStatusText: document.getElementById('videoStatusText'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            errorOverlay: document.getElementById('errorOverlay'),
            fullscreenBtn: document.getElementById('fullscreenBtn')
        };

        // 状态
        this.isConnected = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.statusCheckInterval = null;

        this.init();
    }

    init() {
        this.setupVideoEvents();
        this.setupFullscreen();
        this.startStatusCheck();
    }

    /**
     * 设置视频事件
     */
    setupVideoEvents() {
        const video = this.elements.videoFeed;
        if (!video) return;

        // 视频加载成功
        video.addEventListener('load', () => {
            this.onVideoLoad();
        });

        // 视频加载错误
        video.addEventListener('error', () => {
            this.onVideoError();
        });

        // 加载进度
        video.addEventListener('progress', () => {
            if (!this.isConnected && video.readyState >= 2) {
                this.onVideoLoad();
            }
        });
    }

    /**
     * 视频加载成功
     */
    onVideoLoad() {
        this.isConnected = true;
        this.retryCount = 0;
        this.updateStatus(true);
        this.hideOverlays();
        console.log('视频流已连接');
    }

    /**
     * 视频加载错误
     */
    onVideoError() {
        if (!this.isConnected) {
            this.retryCount++;

            if (this.retryCount >= this.maxRetries) {
                this.updateStatus(false);
                this.showError();
                console.error('视频流连接失败');
            }
        }
    }

    /**
     * 更新连接状态显示
     */
    updateStatus(connected) {
        if (this.elements.videoStatusDot) {
            this.elements.videoStatusDot.classList.toggle('connected', connected);
        }
        if (this.elements.videoStatusText) {
            this.elements.videoStatusText.textContent = connected ? '已连接' : '未连接';
        }
    }

    /**
     * 隐藏所有覆盖层
     */
    hideOverlays() {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.style.display = 'none';
        }
        if (this.elements.errorOverlay) {
            this.elements.errorOverlay.style.display = 'none';
        }
    }

    /**
     * 显示加载状态
     */
    showLoading(message = '正在连接视频流...') {
        if (this.elements.loadingOverlay) {
            this.elements.loadingOverlay.style.display = 'flex';
            const text = this.elements.loadingOverlay.querySelector('span');
            if (text) text.textContent = message;
        }
        if (this.elements.errorOverlay) {
            this.elements.errorOverlay.style.display = 'none';
        }
    }

    /**
     * 显示错误状态
     */
    showError() {
        this.hideOverlays();
        if (this.elements.errorOverlay) {
            this.elements.errorOverlay.style.display = 'flex';
        }
    }

    /**
     * 设置全屏功能
     */
    setupFullscreen() {
        const btn = this.elements.fullscreenBtn;
        const container = document.querySelector('.video-wrapper');

        if (!btn || !container) return;

        btn.addEventListener('click', () => {
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                container.requestFullscreen().catch(err => {
                    console.log('全屏模式不可用:', err);
                });
            }
        });

        // 监听全屏变化
        document.addEventListener('fullscreenchange', () => {
            const isFullscreen = !!document.fullscreenElement;
            btn.innerHTML = isFullscreen
                ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path></svg>'
                : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path></svg>';
            btn.title = isFullscreen ? '退出全屏' : '全屏';
        });
    }

    /**
     * 开始状态检查
     */
    startStatusCheck() {
        this.statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch('/status');
                const data = await response.json();

                if (data.status === 'running' && !this.isConnected) {
                    // 服务器运行中但视频未连接，刷新视频
                    const video = this.elements.videoFeed;
                    if (video) {
                        video.src = '/video_feed?' + Date.now();
                    }
                }
            } catch (e) {
                // 忽略错误
            }
        }, 5000);
    }

    /**
     * 刷新视频流
     */
    refresh() {
        const video = this.elements.videoFeed;
        if (video) {
            this.showLoading('重新连接...');
            this.isConnected = false;
            this.retryCount = 0;
            video.src = '/video_feed?' + Date.now();
        }
    }

    /**
     * 销毁
     */
    destroy() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
    }
}

// 导出到全局
window.VideoStream = VideoStream;
