import numpy as np
import librosa
def note_list_mean(note_list: list):
    hz_list = np.array([librosa.note_to_hz(note) for note in note_list])
    return np.mean(hz_list)