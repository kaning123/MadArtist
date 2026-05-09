import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
import file_lib as fl
import argparse
import json
import os

__INNER_VERSION__ = "Alpha_0.0.1_202605"
OUTPUT_DIR = fl.merge_dir_txt2(fl.get_my_dir(), "Output")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    
def detect_voice_segments(
    audio_path,
    sr=22050,
    top_db=25,        # 低于这个分贝的视为静音，人声通常高于-25dB
    min_duration=0.1  # 人声片段最小持续时间（秒），过滤掉噪声
):
    """
    检测音频中的人声片段，返回(起始时间, 结束时间)列表
    """
    # 加载音频
    y, sr = librosa.load(audio_path, sr=sr)
    
    # 计算静音区间（返回静音的区间）
    non_silent_intervals = librosa.effects.split(y, top_db=top_db)
    
    # 转换为时间（秒）
    voice_segments = []
    for start, end in non_silent_intervals:
        start_sec = start / sr
        end_sec = end / sr
        duration = end_sec - start_sec
        
        # 过滤掉太短的片段（可能是噪声）
        if duration >= min_duration:
            voice_segments.append((start_sec, end_sec))
    
    return y, sr, voice_segments

def cut_and_save_voices(
    audio_path,
    output_dir=fl.merge_dir_txt2(fl.get_my_dir(), "Output"),
    sr=22050,
    top_db=25,
    min_duration=0.1,
):
    """
    切割音频中的人声片段，保存到指定目录
    """
    audio_path = Path(audio_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # 检测人声片段
    y, sr, segments = detect_voice_segments(
        audio_path, sr=sr, top_db=top_db, min_duration=min_duration
    )
    
    if not segments:
        print("未检测到有效人声片段")
        return []
    
    print(f"检测到 {len(segments)} 个人声片段")
    paths = []
    # 保存每个片段
    for i, (start_sec, end_sec) in enumerate(segments):
        start_idx = int(start_sec * sr)
        end_idx = int(end_sec * sr)
        segment = y[start_idx:end_idx]
        
        out_path = output_dir / f"{audio_path.stem}_voice_{i+1}.wav"
        sf.write(out_path, segment, sr)
        print(f"保存片段 {i+1}: {out_path} ({start_sec:.2f}s ~ {end_sec:.2f}s)")
        paths.append(out_path)
    
    return paths

if __name__ == "__main__":
    print(f"MadArtist VoiceSplit Module - {__INNER_VERSION__}")
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio_path", "-a", type=str, help="音频文件路径")
    parser.add_argument("--output_dir", "-o", type=str, default=fl.merge_dir_txt2(fl.get_my_dir(), "Output"), help="输出目录")
    parser.add_argument("--config_path", "-c", type=str, default=None, help="配置文件路径")
    args = parser.parse_args()
    if args.config_path is not None:
        with open(args.config_path, "r") as f:
            config = json.load(f)
        cut_and_save_voices(args.audio_path, args.output_dir,**config)
    else:
        cut_and_save_voices(args.audio_path, args.output_dir)