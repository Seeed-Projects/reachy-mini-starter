#!/usr/bin/env python3
"""Reachy Mini 音频播放器 - 支持在线 URL 和本地文件

这个脚本展示如何使用 Reachy Mini 的媒体播放器功能。
支持从本地文件或在线 URL 播放音频。

功能:
- 自动识别音频源类型 (本地文件 / 在线 URL)
- 支持多种音频格式 (WAV, MP3, FLAC, OGG)
- 自动音频处理 (转单声道, 重采样)
- 临时文件自动清理
"""

import logging
import tempfile
import time
import os
from pathlib import Path
import sys

import numpy as np
import requests
import scipy.signal
import soundfile as sf

from reachy_mini import ReachyMini

logging.basicConfig(level=logging.INFO)


def play_audio_source(
    mini,
    source: str,
    resample: bool = True,
    target_sr: int = 16000,
):
    """
    播放音频 (自动识别是在线 URL 还是本地路径)

    Args:
        mini: ReachyMini 实例
        source: 音频地址，可以是 URL (http开头) 或 本地绝对路径
        resample: 是否重采样
        target_sr: 目标采样率
    """

    temp_path = None
    file_to_play = None
    is_downloaded = False

    try:
        # ================= 判断源类型 =================
        if source.startswith("http://") or source.startswith("https://"):
            # --- 分支 A: 在线 URL ---
            print(f"检测到在线链接，正在下载: {source}")

            response = requests.get(source, timeout=30)
            response.raise_for_status()

            # 确定后缀
            if source.endswith(".mp3"):
                suffix = ".mp3"
            elif source.endswith(".flac"):
                suffix = ".flac"
            elif source.endswith(".ogg"):
                suffix = ".ogg"
            else:
                suffix = ".wav"

            # 写入临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name

            print(f"已下载到临时文件: {temp_path}")
            file_to_play = temp_path
            is_downloaded = True  # 标记为下载文件，播放完需要删除

        else:
            # --- 分支 B: 本地文件 ---
            print(f"检测到本地路径: {source}")
            local_path = Path(source)
            if not local_path.exists():
                print(f"错误: 找不到文件 {source}")
                return

            file_to_play = str(local_path)
            is_downloaded = False  # 本地文件播放完不删除

        # ================= 音频处理与播放 =================
        print("正在读取/解码音频...")
        data, samplerate = sf.read(file_to_play, dtype="float32")

        print(f"原始信息:")
        print(f"  采样率: {samplerate} Hz")
        print(f"  声道: {data.shape[1] if len(data.shape) > 1 else 1}")

        # 1. 转换为单声道
        if data.ndim > 1:
            print("转换为单声道...")
            data = np.mean(data, axis=1)

        # 2. 重采样
        if resample and samplerate != target_sr:
            print(f"重采样到 {target_sr} Hz...")
            num_samples = int(len(data) * (target_sr / samplerate))
            data = scipy.signal.resample(data, num_samples)

        # 3. 计算准确时长 (关键修复)
        duration = len(data) / target_sr
        print(f"预计播放时长: {duration:.2f} 秒")

        # 4. 开始播放
        print("\n开始播放...")
        mini.media.start_playing()

        chunk_size = 1024
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            mini.media.push_audio_sample(chunk)

        # 5. 等待播放完成 (修复了之前的 1s 问题)
        print(f"等待播放结束...")
        time.sleep(duration + 0.5)  # 多给 0.5s 缓冲

        mini.media.stop_playing()
        print("播放完成!")

    except requests.RequestException as e:
        print(f"下载失败: {e}")
    except Exception as e:
        print(f"播放过程出错: {e}")
    finally:
        # ================= 清理工作 =================
        # 只有当文件是下载的临时文件时，才执行删除
        if is_downloaded and temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("临时文件已清理")
            except OSError:
                pass


def main():
    """主函数测试 - 演示模式"""

    # 测试音频源列表
    test_sources = [
        # 本地文件测试 (请确保文件存在，否则会报错)
        # "/path/to/your/local/audio.wav",

        # 在线文件测试 (示例)
        # "https://example.com/audio.wav",
    ]

    with ReachyMini() as mini:
        print("=== Reachy Mini 音频播放器 ===\n")

        if not test_sources or (len(test_sources) == 1 and test_sources[0].startswith("#")):
            print("未配置测试音频源!")
            print("\n使用方法:")
            print("  1. 在脚本中修改 test_sources 列表")
            print("  2. 或使用命令行参数: python audio_player.py <音频路径或URL>")
            return

        for src in test_sources:
            if not src.startswith("#"):
                print(f"\n{'='*60}")
                play_audio_source(mini, src)


if __name__ == "__main__":
    # 命令行支持
    if len(sys.argv) > 1:
        input_source = sys.argv[1]
        with ReachyMini() as mini:
            play_audio_source(mini, input_source)
    else:
        main()
