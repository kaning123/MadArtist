import asyncio
import edge_tts
from edge_tts import VoicesManager
async def list_voices():
    voices = await VoicesManager.create()
    filtered_voices = voices.find(Language="zh", Locale="zh-CN")
    ret = []
    for voice in filtered_voices:
        ret.append(voice)
        print(f"语音名称: {voice['Name']}, 性别: {voice['Gender']}, 语言: {voice['Language']}")
    return ret

async def say_(text, voice, save_path, **kwargs):
    communicate = edge_tts.Communicate(text, voice, **kwargs)
    await communicate.save(save_path)
if __name__ == "__main__":
    a = asyncio.run(list_voices())[0]["ShortName"]
    asyncio.run(say_("你好", a, "output.mp3",pitch = "+20Hz"))