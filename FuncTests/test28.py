import librosa
import numpy as np
import matplotlib.pyplot as plt
# 替换为你的音频文件路径
audio_path = r"D:\Documents\Downloads\我,是.wav"

# 加载音频，sr=None 保持原始采样率，或指定目标采样率如 sr=16000
y, sr = librosa.load(audio_path, sr=None) 

# 定义搜索基频的范围（单位：Hz），这对结果准确性至关重要
fmin = librosa.note_to_hz("C2") 
fmax = librosa.note_to_hz("C7") 

# 执行 pYIN 音高追踪
f0, voiced_flag, voiced_probs = librosa.pyin(
    y, 
    fmin=fmin, 
    fmax=fmax, 
    sr=sr
)

f0_modified = f0[~np.isnan(f0)] 

# 打印结果概览
print(f"提取到的音高序列长度（帧数）: {len(f0)}")
print(f"前10个音高值 (Hz): {f0[:10]}")
print(f"平均音高 (Hz): {np.mean(f0_modified)}")

# 绘制音高序列
plt.figure(figsize=(10, 4))
plt.plot(f0, color='red', label='Original F0')
plt.plot(f0_modified, color='blue', label='Extracted F0')
plt.xlabel('Frame Index')
plt.ylabel('F0 (Hz)')
plt.title('Extracted F0 Sequence')
plt.legend()
plt.grid(True)
plt.show()
