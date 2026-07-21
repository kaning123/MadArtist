import librosa, librosa.display
import matplotlib.pyplot as plt
import numpy as np
# 加载音频
y, sr = librosa.load("D:/Documents/Downloads/我,是.wav", sr=None)
# 计算梅尔频谱
mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=sr/2)
# 转换为dB刻度
mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
# 可视化
plt.figure(figsize=(10, 4))
librosa.display.specshow(mel_spec_db, sr=sr, x_axis='time', y_axis='mel', fmax=sr/2)
plt.colorbar(format='%+2.0f dB')
plt.title('Mel Spectrogram')
plt.tight_layout()
plt.show()
