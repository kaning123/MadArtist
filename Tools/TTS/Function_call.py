import file_lib as fl
import requests
import asyncio
import json
import aiohttp
import os
from pathlib import Path
import uuid
import traceback
import log_lib
import zipfile
import retrying
from rich.console import Console


console = Console()
logger = log_lib.LogStream("Function_Call_Debug",).logger
STORAGE_DIR = fl.merge_dir_txt2(fl.get_my_dir(), "Storage")
CONFIG_DIR = fl.merge_dir_txt2(STORAGE_DIR, "Config")
LOCAL_TEMP_DIR = fl.merge_dir_txt2(fl.get_my_dir(), "Temp")

if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)
if not os.path.exists(LOCAL_TEMP_DIR):
    os.makedirs(LOCAL_TEMP_DIR)

class MadTempFile:
    def __init__(self,
                 path,
                 logger: log_lib.LogStream = log_lib.LogStream("MadTempFile_Debug"),
                 mode: str = "rb",):
        self.path = Path(path)
        self.mode = mode
        self.logger = logger.logger
        self.fileobj = None
        self.logger.debug(f"file: {self.path}, exists: {self.path.exists()}")
        self.open()

    def open(self):
        self.fileobj = open(self.path, self.mode)
        self.logger.debug(f"file: {self.path}, opened: {self.fileobj}")
        return self.fileobj
    
    def close(self):
        if self.fileobj is not None:
            self.fileobj.close()
            self.logger.debug(f"file: {self.path}, closed: {self.fileobj}")
            self.fileobj = None

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()  # Close the file when exiting the context manager
        os.remove(self.path)  # Remove the file from the file system
        self.logger.debug(f"file: {self.path}, removed: {not self.path.exists()}")
        
    def __enter__(self):
        return self

class MadFileBatch:
    def __init__(self, 
                 files: list[Path]|list[str]|str|Path):
        self.open_pool = []
        if not isinstance(files, list):
            if isinstance(files, str):
                files = [files]
            elif isinstance(files, Path):
                files = [files]
            else:
                raise TypeError("files should be list, str or Path")
        self.files = [Path(file) if isinstance(file, str) else file for file in files]

    def to_requests_files(self,
                          static_name=None):
        self.static_name = static_name
        ret = []
        if static_name is not None:
            for file in self.files:
                logger.debug(f"file: {file}, exists: {file.exists()}")
                if not file.exists():
                    raise FileNotFoundError(f"file {file} does not exist")

                f = open(file, "rb") # Open the file in binary read mode
                self.open_pool.append(f) # Add the file to the open pool
                obj = (self.static_name, (file.name, f, "application/octet-stream"))
                ret.append(obj)
        else:
            for file in self.files:
                if not file.exists():
                    raise FileNotFoundError(f"file {file} does not exist")

                f = open(file, "rb") # Open the file in binary read mode
                self.open_pool.append(f) # Add the file to the open pool
                obj = (f"{file.name}_{uuid.uuid4()}", (file.name, f, "application/octet-stream"))
                ret.append(obj)
        return ret
    def cleanup(self):
        for f in self.open_pool:
            f.close()
        self.open_pool = []
    def __del__(self):
        self.cleanup()

def flite_path(obj:list[str]|str, input_:list[str]|str):
    ret = []
    if isinstance(obj, str):
        obj = [obj]
    if isinstance(input_, str):
        input_ = [input_]
    for o in obj:
        for i in input_:
            if o in i:
                ret.append(i)
    logger.debug(f"obj: {obj}, input_: {input_}")
    logger.debug(f"ret: {ret}")
    return ret

class MadPthFileBatch(MadFileBatch):
    def __init__(self, files: list[Path]|list[str]|str|Path):
        files = flite_path([".pth"], files) # type: ignore
        super().__init__(files)

class MadWavFileBatch(MadFileBatch):
    def __init__(self, files: list[Path]|list[str]|str|Path):
        files = flite_path([".wav"], files) # type: ignore
        super().__init__(files)

class MadIndexFileBatch(MadFileBatch):
    def __init__(self, files: list[Path]|list[str]|str|Path):
        files = flite_path([".index"], files) # type: ignore
        super().__init__(files)
        
with open(fl.merge_dir_txt2(CONFIG_DIR, "Function_Call_Consts.json"), "r") as f:
    CONSTS = json.load(f)

def change_list(l:list[Path] | list[str] | Path | str,
                RaiseFileNotFoundError=True):
    ret = {}
    if isinstance(l, str):
        l = [Path(l)]
    elif isinstance(l, Path):
        l = [l]
    elif isinstance(l, list):
        if not all(isinstance(i, (str, Path)) for i in l):
            raise TypeError("all items in list should be str or Path")
        elif all(isinstance(i, str) for i in l):
            l = [Path(i) for i in l]
        else:
            l = [i for i in l if i.exists()] #type: ignore
    else:
        raise TypeError("l should be list, str or Path")
    if isinstance(l[0], Path):
        l = l
    elif isinstance(l[0], str):
        l = [Path(i) for i in l]
    for i in l:
        if not i.exists():
            if RaiseFileNotFoundError:
                raise FileNotFoundError(f"file {i} does not exist")
            else:
                continue
        else:
            ret[i.name] = i
    return ret

async def get_list() -> list:
    res = requests.get("http://localhost:8848/get/list/BaseVoiceGenerator")
    return res.json()

async def Generate_BaseVoice(Voice, text):
    if isinstance(Voice, str):
        Voice = Voice
    elif isinstance(Voice, dict):
        Voice = Voice["ShortName"]
    elif isinstance(Voice, list):
        Voice = Voice[0]["ShortName"]
    else:
        raise TypeError("Voice should be str, dict or list")
    url = f"http://localhost:8848/get/wav/BaseVoiceGenerator/{Voice}/{text}"
    res = requests.get(url)
    with open(str(fl.merge_dir_txt2(STORAGE_DIR, f"{Voice}.wav")), "wb") as f:
        f.write(res.content)

async def post_files(url, files):
        res = requests.post(url, files=files)
        return res.json()

async def post_files2(url, 
                      files,
                      ReturnJson=False):
    res = requests.post(url, files=files)
    if ReturnJson:
        return res.json()
    else:
        return res
    
async def upload_voice(files):
    url = "http://localhost:8848/upload/voice"
    res = requests.post(url, files=files)
    return res.json()

async def get_voice_list():
    url = "http://localhost:8848/get/list/VoiceChanger/Voice"
    res = requests.get(url)
    try:
        logger.debug(f"Response JSON: {res.json()}")
        ret = res.json()["files_"]
    except:
        traceback.print_exc()
        return []
    return ret

async def get_voice_list_name():
    url = "http://localhost:8848/get/list/VoiceChanger/voice_pth/name"
    res = requests.get(url)
    try:
        logger.debug(f"Response JSON: {res.json()}")
        ret = res.json()["files_"]
    except:
        traceback.print_exc()
        return []
    return ret

async def upload_index(files):
    url = "http://localhost:8848/upload/index"
    res = requests.post(url, files=files)
    return res.json()

async def get_index_list():
    url = "http://localhost:8848/get/list/VoiceChanger/Index"
    res = requests.get(url)
    try:
        logger.debug(f"Response JSON: {res.json()}")
        ret = res.json()["files_"]
    except:
        traceback.print_exc()
        return []
    return ret

async def get_index_list_name():
    url = "http://localhost:8848/get/list/VoiceChanger/voice_index/name"
    res = requests.get(url)
    try:
        logger.debug(f"Response JSON: {res.json()}")
        ret = res.json()["files_"]
    except:
        traceback.print_exc()
        return []
    return ret

async def GetVoice_Dict():
    res = await get_voice_list()
    ret = change_list(res)
    return ret

async def GetIndex_Dict():
    res = await get_index_list()
    ret = change_list(res)
    return ret

async def parse_name(a:str|Path,
                     ftype:str,
                     HowToGetDict):
    if not ftype.startswith("."):
        ftype = "." + ftype
    VoicePth = str(a)
    if  not os.path.exists(VoicePth):
        if not str(VoicePth).endswith(ftype):
            VoicePth = str(VoicePth) + ftype
        VoicePth_ = await HowToGetDict()
        logger.debug(f"VoicePth_: {VoicePth_}")
        VoicePth = VoicePth_[VoicePth]
    elif not os.path.exists(VoicePth):
        VoicePth = str(VoicePth)
    elif os.path.exists(VoicePth):
        batch = MadPthFileBatch(VoicePth)
        await upload_voice(batch.to_requests_files(static_name="files"))
        name = Path(VoicePth).name
        VoicePth_ = await GetVoice_Dict()
        VoicePth = VoicePth_[name]
    return VoicePth

async def ChangeVoice(VoicePth:str|Path,
                      VoiceIndex:str|Path,
                      WavFileBatch:MadWavFileBatch,
                      OutputPath:str|Path = "",
                      CleanUpFileBatch:bool=True,
                      ):
    VoicePth = await parse_name(VoicePth, "pth", GetVoice_Dict)
    VoiceIndex = await parse_name(VoiceIndex, "index", GetIndex_Dict)
    url = f"http://localhost:8848/change/voice/batch/{VoicePth}/{VoiceIndex}"
    files = WavFileBatch.to_requests_files(static_name="files")
    res = await post_files2(url, files)
    if CleanUpFileBatch:
        WavFileBatch.cleanup()
    if OutputPath != "":
        with MadTempFile(fl.merge_dir_txt2(LOCAL_TEMP_DIR, f"Temp_{uuid.uuid4()}.zip"),
                        mode = "wb") as TempZipFile:
            TempZipFile.fileobj.write(res.content)
            TempZipFile.fileobj.close()
            with zipfile.ZipFile(TempZipFile.path, "r") as zip_ref:
                zip_ref.extractall(OutputPath)
    return res

async def WrappedChangeVoice(VoicePth: str | Path,
                      VoiceIndex: str | Path,
                      WavFileBatch: MadWavFileBatch,
                      OutputPath: str | Path = "",
                      CleanUpFileBatch: bool = True,
                      retrying = True,
                      r_times = 3,
                      r_wait = 2,
                      r_count = 0):
    try:
        res = await ChangeVoice(VoicePth,
                                VoiceIndex, 
                                WavFileBatch, 
                                OutputPath, 
                                CleanUpFileBatch)
        return res
    except Exception as e:
        if retrying and r_count < r_times:
            logger.error(f"Error: {e}")
            logger.error(f"Retrying in {r_wait} seconds...")
            await asyncio.sleep(r_wait)
            return await WrappedChangeVoice(VoicePth, 
                                            VoiceIndex, 
                                            WavFileBatch,
                                            OutputPath, 
                                            CleanUpFileBatch, 
                                            retrying, 
                                            r_times, 
                                            r_wait, 
                                            r_count + 1)
        else:
            logger.error(f"Error: {e}")
            console.print_exception(show_locals=True)

if __name__ == '__main__':
    #with open(r"D:\Desktop\Dev\MadArtist\output_fast.wav","rb") as f:
    wavs = MadWavFileBatch([r"D:\Desktop\Dev\MadArtist\output_fast.wav"])
    indexs = asyncio.run(get_index_list_name())
    pths = asyncio.run(get_voice_list_name())
    print("Indexs:", indexs)
    print("Pths:", pths)
    print(asyncio.run(WrappedChangeVoice(pths[0], 
                                         indexs[2], 
                                         wavs, 
                                         fl.merge_dir_txt2(STORAGE_DIR, 
                                                           "Audio",
                                                           "Audio_Generate_" + str(uuid.uuid4())),
                                         r_times=5)))
    if False:
        files = MadFileBatch(["Servers/VoiceChange/Main/Build_/ThirdParty/RVC/logs/guanguanV1.index" 
                             ,"Servers/VoiceChange/Main/Build_/ThirdParty/RVC/logs/keruanV1.index" 
                             ,"Servers/VoiceChange/Main/Build_/ThirdParty/RVC/logs/kikiV1.index"])
        f = files.to_requests_files(static_name="files") 
        res = asyncio.run(upload_index(f))
        print(res)
        del files