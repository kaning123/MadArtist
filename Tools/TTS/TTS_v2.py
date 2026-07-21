import sys
from .Support import TxtParse
import rpyc
import numpy as np
import scipy.io.wavfile as wavfile
import traceback
import librosa
from . import Support
import copy
import uuid
from . import file_lib as fl
from . import file_lib_v2 as flv2
ROOT_DIR = fl.get_parent_dir(fl.get_my_dir(),2)
import sys
new_path = copy.deepcopy(sys.path)
sys.path.append(str(ROOT_DIR))

try:
    import Tools.VoiceSplit as VoiceSplit
except ImportError:
    sys.path = new_path
    raise ImportError("Tools.AutoTranslate module not found.")
sys.path = new_path
connection = rpyc.connect("localhost", 5418)

def Change_voice_pth(vc_path):
    return connection.root.get_vc(vc_path)

def VoiceChangeSingle(audio_path, 
                      index_path,
                      note: str | None = None, 
                      ifChangeVoicePth=False,
                      VoicePth=None,
                      retry=3,
                      depth=0):
    
    if note is not None:  # Convert note to Hz if provided
        to_hz = librosa.note_to_hz(note)
        diff = Support.audio_f0_to_semitones(audio_path, to_hz)
    else:
        diff = 0

    try:
        if ifChangeVoicePth:
            if VoicePth is None:
                raise ValueError("VoicePth is None")
            VoicePth = Change_voice_pth(VoicePth)
        else:
            ret = connection.root.vc_single__(audio_path, 
                                              index_path, 
                                              vc_transform0 = diff)
            return ret[0]
    except Exception:
        traceback.print_exc()
        if depth < retry:
            return VoiceChangeSingle(audio_path, 
                                     index_path,
                                     ifChangeVoicePth=ifChangeVoicePth,
                                     VoicePth=VoicePth,
                                     retry=retry,
                                     depth=depth+1)
        else:
            raise RuntimeError(f"Failed to change voice after retrying {depth} times.")

def VoiceChangeMulti(audio_paths, 
                     index_paths,
                     notes: list[str | None] | None = None, 
                     ifChangeVoicePth=False,
                     VoicePth=None,):
    ret = []
    try:
        if notes is None:
            notes = [None for _ in audio_paths]
        if ifChangeVoicePth:
            if VoicePth is None:
                raise ValueError("VoicePth is None")
            VoicePth = Change_voice_pth(VoicePth)
        if isinstance(audio_paths, str):
            audio_paths = [audio_paths]
            index_paths = [index_paths[0]]
        elif isinstance(index_paths, str):
            index_paths = [index_paths for _ in audio_paths]
        for audio_path, index_path, note in zip(audio_paths, index_paths, notes):
            ret.append(VoiceChangeSingle(audio_path, 
                                         index_path,
                                         note=note,))
        return ret
    except Exception:
        traceback.print_exc()
        raise RuntimeError("Failed to change voice.")

def TTS_Main(texts: list[str], 
             notes: list[list[str | None]] | None = None,
             VoicePth = None,
             IndexPath = None,
             BaseVoiceGenerator: str = "edge_tts_based_engine",
             TxtParser: str = "zh_pinyin",):
    
    BaseVoiceGenerator_ = TxtParse.GetGenerator(BaseVoiceGenerator)
    if BaseVoiceGenerator_ is None:
        raise ValueError("BaseVoiceGenerator not found.")
    BaseVoiceGenerator_ = BaseVoiceGenerator_.Main()
    TxtParser_ = TxtParse.get_parser(TxtParser)
    if TxtParser_ is None:
        raise ValueError("TxtParser not found.")
    if notes is None:
        raise ValueError("notes is None.")
    
    if len(texts) != len(notes):
        raise ValueError("texts and notes must have the same length.")
    if VoicePth is None:
        raise ValueError("VoicePth is None.")
    texts = TxtParser_(texts)
    paths = []
    for text, note in zip(texts, notes):
        if not isinstance(note, list):
            raise ValueError("note must be a list.")
        audio_path = BaseVoiceGenerator_.generate(text, note)
        if audio_path is None:
            raise ValueError("Audio path is None.")
        with flv2.TempDir(f"TTSTempDir_{uuid.uuid4().hex}") as temp_dir:
            temp_dir_path = temp_dir.path
            ret = VoiceSplit.cut_and_save_voices(audio_path, output_dir=temp_dir_path)
            res = VoiceChangeMulti(ret, IndexPath, notes=note, VoicePth=VoicePth, ifChangeVoicePth=True)
            paths.append(res)
    return paths

if __name__ == "__main__":
    pass