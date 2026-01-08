"""
Reachy Mini 音频推送演示 (Demo 5)

将电脑的音频实时推送到 Reachy Mini 机器人进行播放。

功能：
1. 捕获电脑的系统音频（输出设备）
2. 实时将音频数据推送到 Reachy Mini
3. 支持多种音频源选择
4. 可视化音频波形

前置条件：
    pip install reachy-mini pyaudio numpy

使用：
    # 列出可用的音频设备
    python audio_streaming.py --list-devices

    # 使用默认音频输出设备
    python audio_streaming.py

    # 指定音频设备
    python audio_streaming.py --device 1

    # 调整缓冲区大小（如果音频卡顿）
    python audio_streaming.py --buffer-size 2048
"""

import argparse
import time
import sys
import math

import numpy as np

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: pyaudio not installed. Install with: pip install pyaudio")

try:
    from reachy_mini import ReachyMini
    REACHY_AVAILABLE = True
except ImportError:
    REACHY_AVAILABLE = False
    print("Warning: reachy-mini not installed. Install with: pip install reachy-mini")


class AudioStreamer:
    """音频流推送控制器"""

    def __init__(self, reachy_mini, device_index=None, sample_rate=None,
                 channels=None, buffer_size=1024, format=pyaudio.paInt16,
                 enable_visualizer=True):
        """
        初始化音频流推送器

        Args:
            reachy_mini: ReachyMini 实例
            device_index: 音频设备索引，None 表示使用默认设备
            sample_rate: 采样率，None 表示使用机器人默认采样率
            channels: 声道数，None 表示使用机器人默认声道数
            buffer_size: 缓冲区大小（帧数）
            format: 音频格式
            enable_visualizer: 是否启用可视化
        """
        self.mini = reachy_mini
        self.device_index = device_index
        self.buffer_size = buffer_size
        self.format = format
        self.enable_visualizer = enable_visualizer

        # 获取机器人音频参数
        if sample_rate is None:
            self.sample_rate = reachy_mini.media.get_output_audio_samplerate()
        else:
            self.sample_rate = sample_rate

        if channels is None:
            self.channels = reachy_mini.media.get_output_channels()
        else:
            self.channels = channels

        # PyAudio 实例
        if PYAUDIO_AVAILABLE:
            self.p = pyaudio.PyAudio()
        else:
            self.p = None
            raise ImportError("PyAudio is required but not installed")

        # 音频流
        self.stream = None

        # 状态
        self.is_streaming = False

        # 统计信息
        self.frames_pushed = 0
        self.start_time = None

    def list_audio_devices(self):
        """列出所有可用的音频设备"""
        if not PYAUDIO_AVAILABLE:
            print("PyAudio 不可用")
            return

        print("\n可用的音频设备:")
        print("=" * 70)
        print(f"{'索引':<6} {'名称':<40} {'采样率':<10} {'输入/输出'}")
        print("-" * 70)

        for i in range(self.p.get_device_count()):
            info = self.p.get_device_info_by_index(i)
            name = info['name']
            max_channels = info['maxOutputChannels']
            sample_rate = int(info['defaultSampleRate'])

            # 只显示输出设备
            if max_channels > 0:
                device_type = "输出"
                print(f"{i:<6} {name:<40} {sample_rate:<10} {device_type}")

        print("=" * 70)
        print("\n提示: 使用 --device 参数指定设备索引")

    def get_default_output_device(self):
        """获取默认输出设备"""
        if not PYAUDIO_AVAILABLE:
            return None

        try:
            # 尝试获取默认输出设备
            device_info = self.p.get_default_output_device_info()
            return device_info['index']
        except Exception as e:
            print(f"Warning: Could not get default output device: {e}")
            # 搜索第一个可用的输出设备
            for i in range(self.p.get_device_count()):
                info = self.p.get_device_info_by_index(i)
                if info['maxOutputChannels'] > 0:
                    return i
        return None

    def setup_audio_stream(self):
        """设置音频流"""
        if self.device_index is None:
            self.device_index = self.get_default_output_device()
            if self.device_index is not None:
                print(f"使用默认音频设备: {self.device_index}")
            else:
                raise RuntimeError("No audio output device found")

        # 验证设备支持请求的参数
        device_info = self.p.get_device_info_by_index(self.device_index)
        max_channels = int(device_info['maxOutputChannels'])

        if self.channels > max_channels:
            print(f"Warning: 设备不支持 {self.channels} 声道，使用 {max_channels} 声道")
            self.channels = max_channels

        try:
            # 打开音频流
            # 注意：这里我们打开输入流来"监听"系统音频
            # Windows 上需要使用 Stereo Mix 或类似的虚拟音频设备
            # Mac 上使用 Soundflower 或 BlackHole
            # Linux 上使用 PulseAudio 或 ALSA 的 monitor device

            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.buffer_size,
                stream_callback=self._audio_callback
            )

            print(f"音频流已设置:")
            print(f"  设备: {device_info['name']}")
            print(f"  采样率: {self.sample_rate} Hz")
            print(f"  声道数: {self.channels}")
            print(f"  缓冲区: {self.buffer_size} 帧")

        except Exception as e:
            raise RuntimeError(f"Failed to setup audio stream: {e}")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        音频回调函数

        注意：这个回调函数仅用于测试，
        实际推送需要在主循环中完成，以避免阻塞问题
        """
        return (in_data, pyaudio.paContinue)

    def start_streaming(self):
        """开始音频流推送"""
        if self.stream is None:
            self.setup_audio_stream()

        # 启动机器人音频播放
        self.mini.media.start_playing()

        self.stream.start_stream()
        self.is_streaming = True
        self.start_time = time.time()
        self.frames_pushed = 0

        print("\n开始音频推送...")
        print("按 Ctrl+C 停止\n")

    def stop_streaming(self):
        """停止音频流推送"""
        self.is_streaming = False

        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # 停止机器人音频播放
        self.mini.media.stop_playing()

        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"\n音频推送已停止")
            print(f"总时长: {elapsed:.1f} 秒")
            print(f"推送帧数: {self.frames_pushed}")

    def stream_audio(self):
        """主音频推送循环"""
        try:
            while self.is_streaming:
                # 读取音频数据
                try:
                    data = self.stream.read(self.buffer_size, exception_on_overflow=False)
                except Exception as e:
                    print(f"Error reading audio: {e}")
                    continue

                # 转换为 numpy 数组
                audio_data = np.frombuffer(data, dtype=np.int16)

                # 归一化到 [-1, 1] 范围（机器人期望 float32）
                audio_data_normalized = audio_data.astype(np.float32) / 32768.0

                # 如果是多声道，混音成单声道（如果需要）
                if self.channels > 1:
                    # 简单的混音：取平均值
                    audio_data_normalized = audio_data_normalized.reshape(-1, self.channels).mean(axis=1)

                # 推送音频到机器人
                try:
                    self.mini.media.push_audio_sample(audio_data_normalized)
                    self.frames_pushed += 1
                except Exception as e:
                    print(f"Error pushing audio: {e}")

                # 可视化（可选）
                if self.enable_visualizer and self.frames_pushed % 10 == 0:
                    self._visualize_audio(audio_data_normalized)

                # 打印统计信息（每秒一次）
                if self.start_time and (time.time() - self.start_time) > 0:
                    elapsed = time.time() - self.start_time
                    if self.frames_pushed % int(self.sample_rate / self.buffer_size) == 0:
                        fps = self.frames_pushed / elapsed
                        print(f"\r推送中... 时长: {elapsed:.1f}s | FPS: {fps:.1f} | 帧: {self.frames_pushed}", end='')

        except KeyboardInterrupt:
            print("\n\n收到停止信号...")
        finally:
            self.stop_streaming()

    def _visualize_audio(self, audio_data):
        """在控制台可视化音频波形"""
        if not self.enable_visualizer:
            return

        # 计算简单的音量条
        rms = np.sqrt(np.mean(audio_data ** 2))
        bar_length = int(rms * 50)
        bar = '█' * min(bar_length, 50)

        # 音量级别
        if rms < 0.1:
            level = "低"
        elif rms < 0.3:
            level = "中"
        else:
            level = "高"

        print(f"\r音量: [{bar:<50}] {level}", end='')

    def cleanup(self):
        """清理资源"""
        self.stop_streaming()

        if self.p is not None:
            self.p.terminate()
            self.p = None


class AudioFileStreamer(AudioStreamer):
    """音频文件推送控制器（用于测试）"""

    def __init__(self, reachy_mini, file_path, enable_visualizer=True):
        """
        初始化音频文件推送器

        Args:
            reachy_mini: ReachyMini 实例
            file_path: 音频文件路径
            enable_visualizer: 是否启用可视化
        """
        self.file_path = file_path
        super().__init__(reachy_mini, enable_visualizer=enable_visualizer)

    def stream_file(self):
        """推送音频文件"""
        try:
            from scipy.io import wavfile
        except ImportError:
            print("Error: scipy is required to read WAV files. Install with: pip install scipy")
            return

        try:
            # 读取 WAV 文件
            sample_rate, audio_data = wavfile.read(self.file_path)
            print(f"读取文件: {self.file_path}")
            print(f"采样率: {sample_rate} Hz")
            print(f"数据形状: {audio_data.shape}")

            # 转换为 float32
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_data = audio_data.astype(np.float32) / 2147483648.0

            # 如果是立体声，转换为单声道
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)

            # 启动机器人音频播放
            self.mini.media.start_playing()

            self.is_streaming = True
            self.start_time = time.time()

            # 分块推送
            chunk_size = self.buffer_size
            total_chunks = len(audio_data) // chunk_size

            print(f"开始推送音频文件... (共 {total_chunks} 块)")
            print("按 Ctrl+C 停止\n")

            for i in range(0, len(audio_data), chunk_size):
                if not self.is_streaming:
                    break

                chunk = audio_data[i:i + chunk_size]

                # 如果是最后一块，填充到完整大小
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant')

                # 推送音频
                self.mini.media.push_audio_sample(chunk)
                self.frames_pushed += 1

                # 打印进度
                progress = (i + chunk_size) / len(audio_data) * 100
                elapsed = time.time() - self.start_time
                print(f"\r进度: {progress:.1f}% | 块: {self.frames_pushed}/{total_chunks} | 时长: {elapsed:.1f}s", end='')

                # 控制推送速度，避免过快
                time.sleep(chunk_size / sample_rate * 0.9)

            print("\n\n音频文件推送完成！")

        except KeyboardInterrupt:
            print("\n\n收到停止信号...")
        except Exception as e:
            print(f"\nError streaming file: {e}")
        finally:
            self.mini.media.stop_playing()
            self.is_streaming = False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reachy Mini 音频推送演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出可用音频设备
  python audio_streaming.py --list-devices

  # 使用默认音频设备推送
  python audio_streaming.py

  # 指定音频设备
  python audio_streaming.py --device 1

  # 调整缓冲区大小（如果音频卡顿）
  python audio_streaming.py --buffer-size 2048

  # 从音频文件推送（用于测试）
  python audio_streaming.py --file test.wav
        """
    )

    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='列出所有可用的音频设备'
    )
    parser.add_argument(
        '--device',
        type=int,
        default=None,
        help='音频设备索引（使用 --list-devices 查看）'
    )
    parser.add_argument(
        '--sample-rate',
        type=int,
        default=None,
        help='采样率（默认使用机器人默认值，通常为 16000 Hz）'
    )
    parser.add_argument(
        '--channels',
        type=int,
        default=None,
        choices=[1, 2],
        help='声道数（1=单声道, 2=立体声，默认使用机器人默认值）'
    )
    parser.add_argument(
        '--buffer-size',
        type=int,
        default=1024,
        help='缓冲区大小（帧数，默认 1024，如果卡顿尝试 2048 或 4096）'
    )
    parser.add_argument(
        '--backend',
        type=str,
        default='default',
        choices=['default', 'default_no_video', 'gstreamer', 'gstreamer_no_video'],
        help='媒体后端（默认 default）'
    )
    parser.add_argument(
        '--file',
        type=str,
        default=None,
        help='从音频文件推送（用于测试，需要安装 scipy）'
    )
    parser.add_argument(
        '--no-visualizer',
        action='store_true',
        help='禁用音频可视化'
    )

    args = parser.parse_args()

    # 检查依赖
    if not PYAUDIO_AVAILABLE:
        print("Error: PyAudio 未安装")
        print("请安装: pip install pyaudio")
        print("\n如果安装失败，请参考:")
        print("  Windows: pip install pipwin && pipwin install pyaudio")
        print("  Mac: brew install portaudio && pip install pyaudio")
        print("  Linux: sudo apt-get install python3-pyaudio")
        sys.exit(1)

    if not REACHY_AVAILABLE:
        print("Error: reachy-mini 未安装")
        print("请安装: pip install reachy-mini")
        sys.exit(1)

    print("=" * 60)
    print("Reachy Mini 音频推送演示")
    print("=" * 60)

    # 创建机器人连接
    print("\n正在连接到 Reachy Mini...")
    try:
        with ReachyMini(media_backend=args.backend) as reachy_mini:
            print("连接成功！")

            # 获取音频参数
            robot_sample_rate = reachy_mini.media.get_output_audio_samplerate()
            robot_channels = reachy_mini.media.get_output_channels()
            print(f"机器人音频参数:")
            print(f"  采样率: {robot_sample_rate} Hz")
            print(f"  声道数: {robot_channels}")

            # 创建音频推送器
            if args.file:
                # 文件模式
                streamer = AudioFileStreamer(
                    reachy_mini,
                    args.file,
                    enable_visualizer=not args.no_visualizer
                )
            else:
                # 实时模式
                streamer = AudioStreamer(
                    reachy_mini,
                    device_index=args.device,
                    sample_rate=args.sample_rate,
                    channels=args.channels,
                    buffer_size=args.buffer_size,
                    enable_visualizer=not args.no_visualizer
                )

            # 列出设备
            if args.list_devices:
                streamer.list_audio_devices()
                return

            print("\n" + "=" * 60)
            print("重要提示:")
            print("=" * 60)
            print("要将电脑音频推送到机器人，您需要:")
            print("")
            print("Windows:")
            print("  1. 打开 '声音控制面板'")
            print("  2. 启用 '立体声混音' (Stereo Mix) 设备")
            print("  3. 将立体声混音设为默认录音设备")
            print("  4. 运行此程序并选择立体声混音设备")
            print("")
            print("Mac:")
            print("  1. 安装 Soundflower 或 BlackHole")
            print("  2. 在音频 MIDI 设置中创建多输出设备")
            print("  3. 将 BlackHole 设为录音输入")
            print("")
            print("Linux:")
            print("  1. 使用 PulseAudio 的 pavucontrol")
            print("  2. 在 '录制' 选项卡中选择 'Monitor of...' 设备")
            print("=" * 60)

            if not args.file:
                input("\n按 Enter 继续...")

                # 再次列出设备
                streamer.list_audio_devices()

                # 如果没有指定设备，询问用户
                if args.device is None:
                    print("\n使用默认设备，或使用 --device 参数指定其他设备")

            print("\n开始音频推送...")
            print("按 Ctrl+C 停止\n")

            # 开始推送
            if args.file:
                streamer.stream_file()
            else:
                streamer.start_streaming()
                streamer.stream_audio()

            # 清理
            streamer.cleanup()

    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
