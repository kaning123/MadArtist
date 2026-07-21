import file_lib as fl
from pathlib import Path
import os
import traceback

MY_DIR = fl.get_my_dir()
TOOLS_DIR = Path(MY_DIR).parent
TEMP_DIR = fl.merge_dir_txt2(MY_DIR, "Temp")

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

import Function_call
from Function_call import MadFileBatch, MadWavFileBatch, MadIndexFileBatch
import pypinyin
from pypinyin import Style, pinyin
import asyncio
import jieba
import uuid
import sys

sys.path.append(str(TOOLS_DIR))
import VoiceSplit.Main as VoiceSplit
sys.path.pop()

import click
import time
import logging
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console

console = Console()
logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%Y.%m.%d-%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click]),]
)
logger = logging.getLogger(__name__)

def process_text(Voice_pth,
                 Voice_index,
                 text):
    # 使用jieba进行分词
    words = jieba.lcut(text)
    pinyin_list = pinyin(words, style=Style.TONE)
    res = ",".join([i[0] for i in pinyin_list])
    BaseVoiceWav = asyncio.run(Function_call.Generate_BaseVoice("zh-CN-XiaoxiaoNeural", 
                                                 res,))
    
    WavTemp = fl.merge_dir_txt2(TEMP_DIR, f"TTS_Request_{uuid.uuid4()}")
    SplitWavDir = fl.merge_dir_txt2(WavTemp, "SplitWavs")
    ResultWav = fl.merge_dir_txt2(WavTemp, "ResultWav")
    
    SplitedWavs = VoiceSplit.cut_and_save_voices(BaseVoiceWav, SplitWavDir,)
    SplitedWavs = MadWavFileBatch(SplitedWavs)

    asyncio.run(Function_call.ChangeVoice(Voice_pth, 
                                          Voice_index, 
                                          SplitedWavs, 
                                          ResultWav))
    
    return ResultWav

if __name__ == '__main__':
    indexs = asyncio.run(Function_call.get_index_list_name())
    pths = asyncio.run(Function_call.get_voice_list_name())
    print(indexs)
    print(pths)
    text = "你好，世界！"
    Voice_pth = pths[0]
    Voice_index = indexs[2]
    result = process_text(Voice_pth, Voice_index, text)
    print(result)
    