"""
Reachy Mini 麦克风录音演示 (Demo 5b)

从 Reachy Mini 的麦克风录制音频，支持实时监听、保存到文件、
声源定位等功能。

功能：
1. 实时从机器人麦克风获取音频
2. 支持实时播放监听（通过电脑扬声器）
3. 保存录音为 WAV 文件
4. 声源定位（DoA）- 需要麦克风阵列支持
5. 音频波形可视化

前置条件：
    pip install reachy-mini pyaudio numpy scipy

使用：
    # 仅录制（无监听）
    python mic_recording.py

    # 录制并实时监听
    python mic_recording.py --monitor

    # 录制并保存到文件
    python mic_recording.py --output recording.wav

    # 显示声源定位
    python mic_recording.py --doa
"""

import argparse
import time
import sys
import math
import os
from datetime import datetime

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


class MicRecorder:
    """麦克风录音控制器"""

    def __init__(self, reachy_mini, enable_monitor=False, enable_doa=False,
                 enable_visualizer=True, output_file=None):
        """
        初始化麦克风录音器

        Args:
            reachy_mini: ReachyMini 实例
            enable_monitor: 是否启用实时监听（通过电脑扬声器）
            enable_doa: 是否启用声源定位
            enable_visualizer: 是否启用可视化
            output_file: 输出文件路径（None 表示不保存）
        """
        self.mini = reachy_mini
        self.enable_monitor = enable_monitor
        self.enable_doa = enable_doa
        self.enable_visualizer = enable_visualizer
        self.output_file = output_file

        # 获取音频参数
        self.sample_rate = reachy_mini.media.get_input_audio_samplerate()
        self.channels = reachy_mini.media.get_input_channels()

        # 录音数据
        self.recorded_data = []
        self.is_recording = False
        self.start_time = None

        # PyAudio 实例（用于监听）
        self.monitor_stream = None
        self.p = None

        # 统计信息
        self.frames_recorded = 0
        self.doa_history = []

        print(f"麦克风参数:")
        print(f"  采样率: {self.sample_rate} Hz")
        print(f"  声道数: {self.channels}")

    def setup_monitor(self):
        """设置监听音频流"""
        if not self.enable_monitor:
            return

        if not PYAUDIO_AVAILABLE:
            print("Warning: PyAudio 不可用，无法启用监听")
            self.enable_monitor = False
            return

        try:
            self.p = pyaudio.PyAudio()

            # 打开输出流用于监听
            self.monitor_stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=1024
            )

            print("监听已启用（音频将通过电脑扬声器播放）")

        except Exception as e:
            print(f"Warning: 无法设置监听: {e}")
            self.enable_monitor = False

    def start_recording(self):
        """开始录音"""
        self.mini.media.start_recording()
        self.is_recording = True
        self.start_time = time.time()
        self.recorded_data = []
        self.frames_recorded = 0
        self.doa_history = []

        print("\n开始录音...")
        print("按 Ctrl+C 停止\n")

    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        self.mini.media.stop_recording()

        # 关闭监听流
        if self.monitor_stream is not None:
            self.monitor_stream.stop_stream()
            self.monitor_stream.close()
            self.monitor_stream = None

        if self.p is not None:
            self.p.terminate()
            self.p = None

        # 打印统计信息
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"\n录音已停止")
            print(f"总时长: {elapsed:.1f} 秒")
            print(f"录制帧数: {self.frames_recorded}")

        # 保存到文件
        if self.output_file and self.recorded_data:
            self.save_to_file()

    def record(self):
        """主录音循环"""
        try:
            while self.is_recording:
                # 获取音频样本
                audio_sample = self.mini.media.get_audio_sample()

                if audio_sample is None:
                    print("Warning: 获取音频样本失败")
                    time.sleep(0.01)
                    continue

                # 确保数据是 float32
                if audio_sample.dtype != np.float32:
                    audio_sample = audio_sample.astype(np.float32)

                # 保存音频数据
                if self.output_file:
                    self.recorded_data.append(audio_sample.copy())

                self.frames_recorded += 1

                # 监听（播放到电脑扬声器）
                if self.enable_monitor and self.monitor_stream is not None:
                    try:
                        # 转换为 bytes 并播放
                        audio_bytes = audio_sample.tobytes()
                        self.monitor_stream.write(audio_bytes)
                    except Exception as e:
                        # 忽略监听错误，避免中断录音
                        pass

                # 声源定位
                if self.enable_doa:
                    self._process_doa()

                # 可视化
                if self.enable_visualizer and self.frames_recorded % 10 == 0:
                    self._visualize_audio(audio_sample)

                # 打印统计信息（每秒一次）
                if self.start_time and self.frames_recorded % int(self.sample_rate / 1000) == 0:
                    elapsed = time.time() - self.start_time
                    fps = self.frames_recorded / elapsed if elapsed > 0 else 0
                    print(f"\r录音中... 时长: {elapsed:.1f}s | FPS: {fps:.1f} | 帧: {self.frames_recorded}", end='')

        except KeyboardInterrupt:
            print("\n\n收到停止信号...")
        finally:
            self.stop_recording()

    def _process_doa(self):
        """处理声源定位"""
        doa_result = self.mini.media.get_DoA()

        if doa_result is not None:
            angle, speech_detected = doa_result

            # 保存历史
            self.doa_history.append({
                'time': time.time(),
                'angle': angle,
                'speech_detected': speech_detected
            })

            # 显示结果
            if speech_detected:
                angle_deg = math.degrees(angle)
                direction = self._angle_to_direction(angle)
                print(f"\n检测到语音！方向: {direction} ({angle_deg:.1f}°)")

    def _angle_to_direction(self, angle_rad):
        """将角度转换为方向描述"""
        angle_deg = math.degrees(angle_rad)

        # 根据 DoA 角度定义
        # 0 弧度 = 左侧
        # π/2 弧度 = 前方/后方
        # π 弧度 = 右侧
        if angle_deg < -135 or angle_deg > 135:
            return "右侧"
        elif -45 <= angle_deg <= 45:
            return "前方"
        elif -135 <= angle_deg < -45:
            return "左侧"
        elif 45 < angle_deg <= 135:
            return "后方"
        else:
            return f"{angle_deg:.0f}°"

    def _visualize_audio(self, audio_sample):
        """可视化音频波形"""
        if not self.enable_visualizer:
            return

        # 计算音量
        if len(audio_sample.shape) == 1:
            # 单声道
            rms = np.sqrt(np.mean(audio_sample ** 2))
        else:
            # 多声道，取平均
            rms = np.sqrt(np.mean(audio_sample ** 2))

        bar_length = int(rms * 40)
        bar = '█' * min(bar_length, 40)

        # 音量级别
        if rms < 0.05:
            level = "静音"
        elif rms < 0.1:
            level = "低"
        elif rms < 0.3:
            level = "中"
        else:
            level = "高"

        print(f"\r音量: [{bar:<40}] {level}", end='')

    def save_to_file(self):
        """保存录音到文件"""
        if not self.recorded_data:
            print("\n没有录音数据可保存")
            return

        try:
            from scipy.io import wavfile
        except ImportError:
            print("\nError: scipy 未安装，无法保存 WAV 文件")
            print("安装: pip install scipy")
            return

        try:
            # 合并所有音频数据
            all_audio = np.concatenate(self.recorded_data)

            # 转换为 int16 格式
            if all_audio.dtype == np.float32:
                # 假设范围是 [-1, 1]
                audio_int16 = (all_audio * 32767).clip(-32768, 32767).astype(np.int16)
            else:
                audio_int16 = all_audio.astype(np.int16)

            # 保存文件
            if self.channels == 1:
                # 单声道
                wavfile.write(self.output_file, self.sample_rate, audio_int16)
            else:
                # 多声道
                wavfile.write(self.output_file, self.sample_rate, audio_int16)

            duration = len(all_audio) / self.sample_rate
            print(f"\n录音已保存到: {self.output_file}")
            print(f"时长: {duration:.1f} 秒")
            print(f"采样率: {self.sample_rate} Hz")
            print(f"声道数: {self.channels}")

        except Exception as e:
            print(f"\nError: 保存文件失败: {e}")

    def analyze_recording(self):
        """分析录音数据"""
        if not self.recorded_data:
            print("\n没有录音数据可分析")
            return

        print("\n" + "=" * 60)
        print("录音分析")
        print("=" * 60)

        # 基本统计
        all_audio = np.concatenate(self.recorded_data)
        duration = len(all_audio) / self.sample_rate
        max_amplitude = np.max(np.abs(all_audio))
        rms = np.sqrt(np.mean(all_audio ** 2))

        print(f"时长: {duration:.2f} 秒")
        print(f"采样数: {len(all_audio)}")
        print(f"最大振幅: {max_amplitude:.4f}")
        print(f"平均音量 (RMS): {rms:.4f}")

        # 声源定位统计
        if self.doa_history:
            speech_events = [d for d in self.doa_history if d['speech_detected']]
            print(f"\n声源定位:")
            print(f"  总检测次数: {len(self.doa_history)}")
            print(f"  检测到语音: {len(speech_events)} 次")

            if speech_events:
                angles = [d['angle'] for d in speech_events]
                avg_angle = np.mean(angles)
                print(f"  平均方向: {self._angle_to_direction(avg_angle)} ({math.degrees(avg_angle):.1f}°)")

        print("=" * 60)


class SimpleRecorder:
    """简单的录音器 - 不带监听"""

    def __init__(self, reachy_mini, output_file=None, duration=None):
        """
        初始化简单录音器

        Args:
            reachy_mini: ReachyMini 实例
            output_file: 输出文件路径
            duration: 录音时长（秒），None 表示手动停止
        """
        self.mini = reachy_mini
        self.output_file = output_file
        self.duration = duration

    def record(self):
        """执行录音"""
        print("开始录音...")

        if self.duration:
            print(f"将录制 {self.duration} 秒...")
        else:
            print("按 Ctrl+C 停止录音")

        self.mini.media.start_recording()

        recorded_data = []
        start_time = time.time()

        try:
            while True:
                # 检查是否达到指定时长
                if self.duration and (time.time() - start_time) >= self.duration:
                    break

                # 获取音频样本
                audio_sample = self.mini.media.get_audio_sample()
                if audio_sample is not None:
                    recorded_data.append(audio_sample.copy())

                # 显示进度
                elapsed = time.time() - start_time
                if self.duration:
                    progress = (elapsed / self.duration) * 100
                    print(f"\r进度: {progress:.1f}% ({elapsed:.1f}/{self.duration}s)", end='')
                else:
                    print(f"\r录音中... {elapsed:.1f}s", end='')

                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\n\n录音已停止")
        finally:
            self.mini.media.stop_recording()

        # 保存文件
        if self.output_file and recorded_data:
            self._save(recorded_data)

        return recorded_data

    def _save(self, recorded_data):
        """保存录音"""
        try:
            from scipy.io import wavfile
        except ImportError:
            print("\nError: scipy 未安装")
            return

        # 合并数据
        all_audio = np.concatenate(recorded_data)

        # 转换为 int16
        if all_audio.dtype == np.float32:
            audio_int16 = (all_audio * 32767).clip(-32768, 32768).astype(np.int16)
        else:
            audio_int16 = all_audio.astype(np.int16)

        sample_rate = self.mini.media.get_input_audio_samplerate()

        try:
            wavfile.write(self.output_file, sample_rate, audio_int16)
            print(f"\n录音已保存: {self.output_file}")
        except Exception as e:
            print(f"\n保存失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Reachy Mini 麦克风录音演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 简单录音（5秒）
  python mic_recording.py --simple --duration 5

  # 录音并保存
  python mic_recording.py --output recording.wav

  # 录音并实时监听
  python mic_recording.py --monitor

  # 录音并显示声源定位
  python mic_recording.py --doa

  # 完整功能（监听 + DoA + 保存）
  python mic_recording.py --monitor --doa --output test.wav
        """
    )

    parser.add_argument(
        '--simple',
        action='store_true',
        help='使用简单录音模式（无可视化、无监听）'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=None,
        help='录音时长（秒），仅用于简单模式'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=str,
        default=None,
        help='输出文件路径（WAV 格式）'
    )
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='启用实时监听（通过电脑扬声器播放）'
    )
    parser.add_argument(
        '--doa',
        action='store_true',
        help='启用声源定位显示'
    )
    parser.add_argument(
        '--no-visualizer',
        action='store_true',
        help='禁用音频可视化'
    )
    parser.add_argument(
        '--backend',
        type=str,
        default='default',
        choices=['default', 'default_no_video', 'gstreamer', 'gstreamer_no_video'],
        help='媒体后端（默认 default）'
    )

    args = parser.parse_args()

    # 检查依赖
    if not REACHY_AVAILABLE:
        print("Error: reachy-mini 未安装")
        print("请安装: pip install reachy-mini")
        sys.exit(1)

    if args.monitor and not PYAUDIO_AVAILABLE:
        print("Error: --monitor 需要 PyAudio")
        print("请安装: pip install pyaudio")
        sys.exit(1)

    print("=" * 60)
    print("Reachy Mini 麦克风录音演示")
    print("=" * 60)

    # 生成默认文件名
    output_file = args.output
    if output_file is None and not args.simple:
        # 自动生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"recording_{timestamp}.wav"

    # 创建机器人连接
    print("\n正在连接到 Reachy Mini...")
    try:
        with ReachyMini(media_backend=args.backend) as reachy_mini:
            print("连接成功！")

            # 获取音频参数
            sample_rate = reachy_mini.media.get_input_audio_samplerate()
            channels = reachy_mini.media.get_input_channels()
            print(f"麦克风参数:")
            print(f"  采样率: {sample_rate} Hz")
            print(f"  声道数: {channels}")

            # 选择模式
            if args.simple:
                # 简单模式
                print("\n使用简单录音模式")
                recorder = SimpleRecorder(
                    reachy_mini,
                    output_file=output_file,
                    duration=args.duration
                )
                recorder.record()

            else:
                # 完整模式
                if output_file:
                    print(f"\n录音将保存到: {output_file}")

                recorder = MicRecorder(
                    reachy_mini,
                    enable_monitor=args.monitor,
                    enable_doa=args.doa,
                    enable_visualizer=not args.no_visualizer,
                    output_file=output_file
                )

                # 设置监听
                if args.monitor:
                    recorder.setup_monitor()

                # 开始录音
                recorder.start_recording()
                recorder.record()

                # 分析录音
                recorder.analyze_recording()

    except KeyboardInterrupt:
        print("\n\n程序已中断")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
