import librosa
import soundfile as sf
import numpy as np
from pathlib import Path

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
    output_dir="voice_segments",
    sr=22050,
    top_db=25,
    min_duration=0.1,
    merge_output=True  # 是否合并成一个无静音的音频
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
        return
    
    print(f"检测到 {len(segments)} 个人声片段")
    
    # 保存每个片段
    for i, (start_sec, end_sec) in enumerate(segments):
        start_idx = int(start_sec * sr)
        end_idx = int(end_sec * sr)
        segment = y[start_idx:end_idx]
        
        out_path = output_dir / f"{audio_path.stem}_voice_{i+1}.wav"
        sf.write(out_path, segment, sr)
        print(f"保存片段 {i+1}: {out_path} ({start_sec:.2f}s ~ {end_sec:.2f}s)")
    
    # 合并成一个无静音的音频
    if merge_output:
        merged = []
        for start_sec, end_sec in segments:
            start_idx = int(start_sec * sr)
            end_idx = int(end_sec * sr)
            merged.append(y[start_idx:end_idx])
        
        merged_y = np.concatenate(merged)
        merged_path = output_dir / f"{audio_path.stem}_merged_no_silence.wav"
        sf.write(merged_path, merged_y, sr)
        print(f"合并完成，无静音音频已保存: {merged_path}")

# ------------------- 使用示例 -------------------
if __name__ == "__main__":
    cut_and_save_voices(
        audio_path="D:/Documents/Downloads/我,是.wav",  # 替换成你的音频路径
        output_dir="voice_segments",
        sr=22050,
        top_db=25,          # 调整这个值控制静音灵敏度，人声通常在-20~-30dB之间
        min_duration=0.1,
        merge_output=True
    )