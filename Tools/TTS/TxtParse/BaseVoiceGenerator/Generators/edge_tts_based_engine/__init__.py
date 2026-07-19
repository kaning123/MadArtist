import edge_tts
import librosa
import os
import json
import pathlib
import asyncio
import uuid
import file_lib as fl
import file_lib_v2 as flv2
import numpy as np
import copy
ROOT_DIR = fl.get_parent_dir(fl.get_my_dir(),6)
import sys
new_path = copy.deepcopy(sys.path)
sys.path.append(str(ROOT_DIR))

try:
    import Tools.AutoTranslate as AutoTranslate
except ImportError:
    sys.path = new_path
    raise ImportError("Tools.AutoTranslate module not found.")

# 加载配置文件
with open(os.path.join(os.path.dirname(__file__), "Config", "Settings.json"), "r") as f:
    settings = json.load(f)

SETTINGS_EXAMPLE = {
    "rate": "+0%",
    "volume": "+0%",
    "pitch": "+10hz"
}

async def list_voices(**FILTER_LIST):
    voices = await edge_tts.VoicesManager.create()
    print(f"flist_voices() called with filters: {FILTER_LIST}")
    filtered_voices = voices.find(**FILTER_LIST)
    ret = []
    for voice in filtered_voices:
        ret.append(voice)
        print(f"语音名称: {voice['Name']}, 性别: {voice['Gender']}, 语言: {voice['Language']}")
    return ret

async def get_voice(txt):
    lang = AutoTranslate.detect_lang(txt)
    voices = await list_voices(Language=lang)
    if voices:
        voice = voices[0]
        return voice
    

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

class Main:
    def __init__(self):
        # 创建音频输出目录（如果不存在）
        self.audio_dir = pathlib.Path(os.path.dirname(__file__)) / "Audio"
        self.audio_dir.mkdir(exist_ok=True)
        self.base = librosa.note_to_hz("A4")  # 默认基准频率 A4
        self.txt = ""
        self.voice = None

    def generate(self, txt: str, note: str | int | float) -> pathlib.Path:
        """
        将文本转换为语音，并根据 note 调整音高。
        :param txt: 要合成的文本
        :param note: 音符（如 'C3'）或频率（Hz），用于设置音高偏移
        :return: 生成的音频文件路径
        """
        # 从设置中读取语速和音量
        self.txt = txt
        rate = settings.get("rate", "+0%")
        volume = settings.get("volume", "+0%")
        # 从设置中读取语音（若无则使用默认）
        self.voice = settings.get("voice", asyncio.run(get_voice(txt)))
        if not self.voice:
            raise RuntimeError("No voice found for the given text.")
        voice = self.voice
        pitch = self._parse_note_to_pitch(note)

        # 生成唯一文件名
        output_path = self.audio_dir / f"voice_{uuid.uuid4().hex}.wav"

        # 异步执行 TTS
        try:
            asyncio.run(self._generate_async(txt, voice, output_path, rate, volume, pitch))

        except Exception as e:
            raise RuntimeError(f"TTS generation failed: {e}")

        return output_path

    async def _generate_async(self, 
                              txt, 
                              voice, 
                              output_path,
                              rate = "+0%", 
                              volume = "+0%", 
                              pitch = "+0hz",):
        """异步执行 TTS 并保存文件"""
        communicate = edge_tts.Communicate(txt, voice, rate=rate, volume=volume, pitch=pitch)
        await communicate.save(str(output_path))

    def _parse_note_to_pitch(self, note):
        """
        将 note 转换为 edge_tts 可接受的音高偏移字符串。
        - 若为 int/float，视为绝对频率（Hz），计算相对于 A4=440Hz 的偏移
        - 若为 str，尝试用 librosa 转为频率，再计算偏移；若失败则假定已是合法偏移字符串（如 "+10Hz"）
        """
        with flv2.TempFile(f"{uuid.uuid4().hex}.wav") as temp_file:
            full_path = temp_file.path
            try:
                asyncio.run(self._generate_async(self.txt, self.voice, full_path))
            except Exception as e:
                raise RuntimeError(f"TTS generation failed: {e}")
            f0_mean = get_audio_f0(full_path)
            self.base = f0_mean
        if isinstance(note, (int, float)):
            freq = float(note)
            offset = freq - self.base  # 参考频率
            return f"{offset:+}Hz"  # 例如 "+10Hz" 或 "-10Hz"
        elif isinstance(note, str):
            try:
                freq = librosa.note_to_hz(note)
                offset = freq - self.base  # 参考频率
                return f"{offset:+}Hz"
            except Exception:
                # 若转换失败，检查是否已包含 "Hz"，若是则直接使用
                if "Hz" in note:
                    return note
                else:
                    raise ValueError(
                        f"Invalid note format: '{note}'. Please provide a valid note like 'C4' "
                        "or a frequency in Hz, or a valid pitch offset like '+10Hz'."
                    )
        else:
            raise TypeError(f"note must be str, int or float, got {type(note)}")

    def EditConfig(self, **kwargs) -> None:
        """
        更新配置并保存到 Settings.json。
        支持更新 rate、volume、pitch、voice 等字段。
        """
        for key, value in kwargs.items():
            if key in settings:
                settings[key] = value
            else:
                # 若字段不存在，可根据需要决定是否添加，这里选择忽略
                pass
        config_path = os.path.join(os.path.dirname(__file__), "Config", "Settings.json")
        with open(config_path, "w") as f:
            json.dump(settings, f, indent=4)