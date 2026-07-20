import librosa
import numpy as np

def get_audio_f0(audio_path):

    # 加载音频，sr=None 保持原始采样率，或指定目标采样率如 sr=16000
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