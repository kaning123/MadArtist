import librosa
import soundfile as sf
import numpy as np

def change_audio_speed(
    input_path: str,
    output_path: str,
    speed_rate: float = 1.25  # 加速倍数：1.25=1.25倍，1.5=1.5倍，0.8=减速
):
    """
    音频加速/减速（不变调）
    :param speed_rate:  >1 加速， <1 减速
    """
    # 加载音频
    y, sr = librosa.load(input_path, sr=None)

    # 核心：变速不变调
    y_stretched = librosa.effects.time_stretch(y, rate=speed_rate)

    # 保存
    sf.write(output_path, y_stretched, sr)
    print(f"✅ 处理完成！速度倍率: {speed_rate} → 输出: {output_path}")

# ------------------- 使用 -------------------
if __name__ == '__main__':
    # 加速 1.5 倍
    change_audio_speed("D:/Documents/Downloads/我,是.wav", "output_fast.wav", speed_rate=2)
    
    # 减速 0.8 倍
    # change_audio_speed("input.wav", "output_slow.wav", speed_rate=0.8)