import librosa
import soundfile as sf
import numpy as np

def string_to_midi(note):
    """把音符字符串(如 'C4')转 MIDI 编号"""
    return librosa.note_to_midi(note)
def pitch_to_midi(freq):
    """频率转 MIDI 编号"""
    return 12 * np.log2(freq / 440.0) + 69
def midi_to_pitch(midi):
    """MIDI 编号转频率"""
    return 440 * 2 ** ((midi - 69) / 12)

def adjust_to_C3(input_file, output_file,max_step = 4):
    y, sr = librosa.load(input_file)
    
    # 估计基频（需要提供音高范围，这里用 C2~C6）
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C6'), sr=sr
    )
    # 取有音高部分的平均基频
    f0_avg = np.mean(f0[voiced_flag])
    
    if np.isnan(f0_avg):
        raise ValueError("无法检测到有效音高")
    
    original_midi = pitch_to_midi(f0_avg)
    target_midi = 48 - 6  # c3
    n_steps = target_midi - original_midi
    n_remaing = n_steps
    y_=y
    if n_steps < 0:
        max_step = -max_step
    while abs(n_remaing) > abs(max_step):
        y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=max_step)
        n_remaing -= max_step
        y = y_shifted
    if n_remaing!= 0:
        y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_remaing)
    
    sf.write(output_file, y_shifted, sr)
    print(f"原始平均音高: {original_midi:.1f} MIDI ({f0_avg:.1f} Hz)")
    print(f"应用半音偏移: {n_steps:.1f}")

# 使用
adjust_to_C3("D:/Documents/Downloads/我,是.wav", "output_C3.wav")
