import fastapi
import asyncio
import uvicorn
import edge_tts
from edge_tts import VoicesManager
import os
from pathlib import Path
from uuid import uuid4

def get_my_dir():
    return os.path.dirname(os.path.abspath(__file__))

def merge_dir_txt2(*TXT):
    return Path(os.path.join(*TXT))

MY_DIR = get_my_dir()
TEMP_DIR = merge_dir_txt2(MY_DIR, "Temp")


async def list_voices():
    voices = await VoicesManager.create()
    filtered_voices = voices.find()
    ret = []
    for voice in filtered_voices:
        ret.append(voice)
        print(f"语音名称: {voice['Name']}, 性别: {voice['Gender']}, 语言: {voice['Language']}")
    return ret

async def say_(text, voice, save_path, **kwargs):
    communicate = edge_tts.Communicate(text, voice, **kwargs)
    await communicate.save(save_path)

def list_voices_():
    return asyncio.run(list_voices())

async def say__(text, voice, **kwargs):
    save_path = merge_dir_txt2(TEMP_DIR, f"{uuid4()}.wav")
    await say_(text, voice, save_path, **kwargs)
    with open(save_path, "rb") as f:
        info = f.read()
    os.remove(save_path)
    return info

app = fastapi.FastAPI()

@app.get("/list/voices")
async def list_voices_api():
    return await list_voices()

@app.get("/generate/{voice_name}/{info}")
async def say_api(voice_name: str, info: str):
    wav_data = await say__(info, voice_name)
    return fastapi.responses.Response(content=wav_data, media_type="audio/wav")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=11451)