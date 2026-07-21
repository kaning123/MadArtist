import librosa
import numpy as np
import math

def get_audio_f0(audio_path):

    # 加载音频，sr=None 保持原始采样率
    y, sr = librosa.load(audio_path, sr=None) 

    # 定义搜索基频的范围（单位：Hz），这对结果准确性至关重要
    fmin = librosa.note_to_hz("C2") 
    fmax = librosa.note_to_hz("C7") 

    # 执行 pYIN 音高追踪
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, 
        fmin=fmin,  # type: ignore
        fmax=fmax,  # type: ignore
        sr=sr
    )

    f0_modified = f0[~np.isnan(f0)] 
    return np.mean(f0_modified)

def hz_diff_to_semitones(delta_hz: float, ref_freq: float) -> float:
    """
    将频率差值（Hz）转换为半音差值，需提供参考频率。

    参数:
        delta_hz: 频率变化量（正数代表升高，负数代表降低）
        ref_freq: 参考频率（基准音频率，必须大于0）

    返回:
        对应的半音数量（1个半音 = 小二度，如钢琴相邻键）
    """
    if ref_freq <= 0:
        raise ValueError("参考频率必须大于 0")
    
    # 如果差值为0，直接返回0，避免计算 log2(1)
    if delta_hz == 0:
        return 0.0
    
    target_freq = ref_freq + delta_hz
    if target_freq <= 0:
        raise ValueError("目标频率必须大于 0（delta_hz 不能小于 -ref_freq）")
    
    # 计算音分数，再除以100得到半音数
    cents = 1200 * math.log2(target_freq / ref_freq)
    return cents / 100.0

def hz2semitones(from_hz, to_hz):
    f1 = from_hz
    f2 = to_hz
    ret = hz_diff_to_semitones(f2 - f1, f1)
    return ret

def audio_f0_to_semitones(audio_path, to_hz):
    f0 = get_audio_f0(audio_path)
    return hz2semitones(f0, to_hz)