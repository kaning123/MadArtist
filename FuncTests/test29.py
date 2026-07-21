import math

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

def main(from_, to_):
    f1 = from_
    f2 = to_
    ret = hz_diff_to_semitones(f2 - f1, f1)
    return ret
# ------------------ 使用示例 ------------------
if __name__ == "__main__":
    # 示例 1: 以国际标准音 A4 (440Hz) 为参考，升高 10Hz
    ref = 440.0
    delta = 10.0
    semitones = hz_diff_to_semitones(-delta, ref)
    print(f"在 {ref}Hz 基础上 +{-delta}Hz 等于 {semitones:.4f} 个半音")
    # 输出: 在 440.0Hz 基础上 +10.0Hz 等于 0.3895 个半音（约 39 音分）

    # 示例 2: 以低音 C (约 130.8Hz) 为参考，同样升高 10Hz
    ref_low = 130.8
    semitones_low = hz_diff_to_semitones(delta, ref_low)
    print(f"在 {ref_low}Hz 基础上 +{delta}Hz 等于 {semitones_low:.4f} 个半音")
    # 输出: 在 130.8Hz 基础上 +10.0Hz 等于 1.2831 个半音（约 1 个全音还多）

    # 示例 3: 直接输入两个绝对频率求差值（避免手动算 delta）
    f1 = 261.63  # C4 (中央C)
    f2 = 293.66  # D4
    # 注意：这里 delta_hz = f2 - f1，ref_freq = f1
    semitones_interval = main(f1, f2)
    print(f"从 {f1}Hz 到 {f2}Hz 是 {semitones_interval:.2f} 个半音")
    # 输出: 从 261.63Hz 到 293.66Hz 是 2.00 个半音（大二度，符合预期）