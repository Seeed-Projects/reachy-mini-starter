/**
 * Demo 17: 主入口文件
 * 初始化控制模块和视频模块
 */

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('Demo 17 初始化中...');

    // 等待所有模块加载
    setTimeout(() => {
        // 初始化机器人控制
        if (typeof RobotControl !== 'undefined') {
            window.robotControl = new RobotControl();
            console.log('机器人控制模块已初始化');
        } else {
            console.error('RobotControl 模块未找到');
        }

        // 初始化视频流
        if (typeof VideoStream !== 'undefined') {
            window.videoStream = new VideoStream();
            console.log('视频流模块已初始化');
        } else {
            console.error('VideoStream 模块未找到');
        }

        console.log('Demo 17 初始化完成');
    }, 100);
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (window.videoStream && typeof window.videoStream.destroy === 'function') {
        window.videoStream.destroy();
    }
});
