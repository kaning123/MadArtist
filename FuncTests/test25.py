import rpyc
import edge_tts
import numpy as np
import scipy.io.wavfile as wavfile
connection = rpyc.connect("localhost", 5418)
a = (connection.root.get_vc("guanguanV1.pth")[2]["value"])
b = connection.root.vc_single__(r"D:\Desktop\Dev\MadArtist\output_fast.wav",a)

# 假设你的元组变量名为 audio_tuple
sample_rate, audio_data = b # sample_rate=40000, audio_data是int16数组

print("Sample Rate:", sample_rate)
print("Audio path:", audio_data)