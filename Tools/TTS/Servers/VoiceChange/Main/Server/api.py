import fastapi
import uvicorn
import requests
import asyncio
import json
import os
import sys
import file_lib as fl
import uuid
import shutil
from pathlib import Path
import tempfile
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import zipfile
import base64
import log_lib
import time
import EasyImDisk
import rich
from rich.console import Console
console = Console()

LOGGER = log_lib.get_logger("API", 
                            fl.merge_dir_txt(fl.get_my_dir(), 
                                             "Log"), 
                            log_lib.DEBUG, 
                            f_display=True).logger


def get_all_file(path,type_):
    txt_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(f'.{type_}'):
                full_path = os.path.join(root, file)
                txt_files.append(full_path)
    return set(txt_files)

def get_all_file_name(path,type_):
    full_paths = get_all_file(path,type_)
    file_names = set()
    for path in full_paths:
        file_names.add(os.path.basename(path))
    return file_names

async def await_file(file_path,
                     timeout: float | int = 1000):
    x = 0
    while not os.path.exists(file_path):
        await asyncio.sleep(0.1)
        x += 0.1
        if x > timeout:
            raise TimeoutError(f"File {file_path} not found after {timeout} seconds")
    return x

TEMP_DIR = fl.merge_dir_txt2(fl.get_my_dir(), "Temp")
shutil.rmtree(TEMP_DIR, ignore_errors=True) if TEMP_DIR.exists() else None
if not TEMP_DIR.exists():
    fl.create_dir(TEMP_DIR)

ROOT_DIR = fl.get_parent_dir(fl.get_my_dir())

BUILD_CONFIG_PATH = fl.merge_dir_txt2(ROOT_DIR, "Config", "Build.json")
if not os.path.exists(BUILD_CONFIG_PATH):
    raise FileNotFoundError(f"Build configuration file not found at {BUILD_CONFIG_PATH}")

with open(BUILD_CONFIG_PATH, "r") as f:
    BUILD_CONFIG = json.load(f)
    RVC_ROOT = BUILD_CONFIG.get("root_location", "")
    if RVC_ROOT == "":
        raise ValueError("root_location must be specified in Build.json")
    
RVC_INJECTION_PATH = fl.merge_dir_txt2(RVC_ROOT, "injected.json")
if not os.path.exists(RVC_INJECTION_PATH):
    raise FileNotFoundError(f"Injection configuration file not found at {RVC_INJECTION_PATH}")

CONFIG_DIR = fl.merge_dir_txt2(fl.get_my_dir(), "Config")
if not CONFIG_DIR.exists():
    fl.create_dir(CONFIG_DIR)

LOCAL_STORAGE_DIR = fl.merge_dir_txt2(fl.get_my_dir(), "LocalStorage")
if not LOCAL_STORAGE_DIR.exists():
    fl.create_dir(LOCAL_STORAGE_DIR)

def get_pth(name):
    if not name.endswith(".pth"):
        name += ".pth"
    pth_path = fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_pth",name)
    if not os.path.exists(pth_path):
        return False,''
    else:
        return True, str(pth_path)

def get_index(name):
    if not name.endswith(".index"):
        name += ".index"
    index_path = fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_index",name)
    if not os.path.exists(index_path):
        return False,''
    else:
        return True, str(index_path)
    
async def change_voice_pth(pth):
    response = requests.post("http://localhost:7897/run/infer_change_voice", json={
        "data": [
            pth,
            0.33,
            0.33,
        ]}).json()
    return response["data"]

async def change_voice_pth_with_name(name):
    if not name.endswith(".pth"):
        name += ".pth"
    if not os.path.exists(name):
        exist, pth = get_pth(name)
        if not exist:
            raise FileNotFoundError(f"Voice pth file not found for name: {name}")
    else:
        pass
    return await change_voice_pth(pth)

with open(os.path.join(str(fl.merge_dir_txt2(CONFIG_DIR, "Function_Call_Consts.json"))),"r") as f:
    CONSTS = json.load(f)

def Update_Injection_weights():
    weights = get_all_file(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_pth",),"pth")
    with open(RVC_INJECTION_PATH, "r") as f:
        injection_config = json.load(f)
        injection_config["weights"] = list(weights)
    with open(RVC_INJECTION_PATH, "w") as f:
        json.dump(injection_config, f, indent=4)

def Update_Injection_index():
    indexs = get_all_file(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_index"), "index")
    with open(RVC_INJECTION_PATH, "r") as f:
        injection_config = json.load(f)
        injection_config["indexs"] = list(indexs)
    with open(RVC_INJECTION_PATH, "w") as f:
        json.dump(injection_config, f, indent=4)

def Clear_Weights_Trash():
    Voice_pth_dir = fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_pth")
    if not os.path.exists(Voice_pth_dir):
        return
    for file in os.listdir(Voice_pth_dir):
        if not file.endswith(".pth"):
            print(f"Deleting non-pth file: {fl.merge_dir_txt2(Voice_pth_dir, file)}")
            os.remove(fl.merge_dir_txt2(Voice_pth_dir,file))

def Clear_Index_Trash():
    Voice_index_dir = fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_index")
    if not os.path.exists(Voice_index_dir):
        return
    for file in os.listdir(Voice_index_dir):
        if not file.endswith(".index"):
            print(f"Deleting non-index file: {fl.merge_dir_txt2(Voice_index_dir, file)}")
            os.remove(fl.merge_dir_txt2(Voice_index_dir,file))

async def Voice_Change(Voice_pth,
                       index_path, 
                       wav_path, 
                       PitchExtraction="pm"):
    await change_voice_pth(Voice_pth)

    if PitchExtraction not in CONSTS["PitchExtraction"]:
        raise ValueError(f"Invalid PitchExtraction method. Supported methods: {CONSTS['PitchExtraction']}")
    
    response = requests.post("http://localhost:7897/run/infer_convert", json={
    "data": [
        0,
        wav_path,
        0,
        {"name":"zip.zip","data":"data:@file/octet-stream;base64,UEsFBgAAAAAAAAAAAAAAAAAAAAAAAA=="},
        PitchExtraction,
        index_path,
        index_path,
        0.75,
        3,
        0,
        0.25,
        0.33,
    ]}).json()

    data = response["data"][1]
    data["data"] = base64.b64decode(data["data"])
    return data

async def Voice_Change_Batch(Voice_pth,index_path, 
                             wav_dir_path, 
                             PitchExtraction = "pm",
                             do_change_voice = True,
                             await_opt: float | int = 100,
                             a: float | int = 0,
                             retry_times = 5,
                             retry_depth = 0):

    if retry_depth > retry_times:
        raise Exception(f"Retry times exceeded: {retry_depth}")

    if do_change_voice:

        await change_voice_pth(Voice_pth)

    output_dir = str(fl.merge_dir_txt2(TEMP_DIR,f"Voice_output_{uuid.uuid4()}"))
    fl.create_dir(Path(output_dir))
    OPT_DIR = str(fl.merge_dir_txt2(RVC_ROOT,"opt"))
    if os.path.exists(OPT_DIR):
        shutil.rmtree(OPT_DIR)
    wav_num = len(os.listdir(wav_dir_path))
    response = requests.post("http://localhost:7897/run/infer_convert_batch", json={
        "data": [
            0,
            wav_dir_path,
            OPT_DIR,
            {"name":"zip.zip","data":"data:@file/octet-stream;base64,UEsFBgAAAAAAAAAAAAAAAAAAAAAAAA=="},
            0,
            PitchExtraction,
            index_path,
            index_path,
            1,
            3,
            0,
            1,
            0.33,
            "wav",
        ]})
    a += await await_file(fl.merge_dir_txt2(OPT_DIR,
                                           "info.json"), 
                         await_opt*wav_num)
    with open(fl.merge_dir_txt2(OPT_DIR,"info.json"), "r") as f:
        info = json.load(f)
        if info["fail"] > 0:
            retrys = info["fail_info"]
            success = info["succ_info"]
            for file in os.listdir(OPT_DIR):
                shutil.move(os.path.join(OPT_DIR, file), output_dir)
            for file in success:
                os.remove(os.path.join(wav_dir_path, file)) # delete successful files
            return Voice_Change_Batch(Voice_pth, index_path, 
                                        wav_dir_path, 
                                        PitchExtraction=PitchExtraction,
                                        do_change_voice=do_change_voice,
                                        await_opt=await_opt,
                                        a=a,
                                        retry_times=retry_times,
                                        retry_depth=retry_depth+1)
    data = response.json()["data"]
    LOGGER.info(f"Response: {data}")
    if not os.path.exists(output_dir):
        fl.create_dir(Path(output_dir))
    if not os.path.exists(OPT_DIR):
        raise Exception(f"Output directory {OPT_DIR} not found")
    for file in os.listdir(OPT_DIR):
        shutil.move(os.path.join(OPT_DIR, file), output_dir)
    return {"output_dir": output_dir, "await_time": a}

async def Voice_Change_Batch_V2(Voice_pth,index_path, 
                             wav_dir_path, 
                             PitchExtraction = "pm",
                             do_change_voice = True,
                             await_opt: float | int = 100,
                             a: float | int = 0,
                             retry_times = 5,
                             retry_depth = 0,
                             retry2 = 5,
                             retry2_depth = 0):
    try:
        retry2_depth += 1
        return await Voice_Change_Batch(Voice_pth, index_path, 
                                        wav_dir_path, 
                                        PitchExtraction=PitchExtraction,
                                        do_change_voice=do_change_voice,
                                        await_opt=await_opt,
                                        a=a,
                                        retry_times=retry_times,
                                        retry_depth=retry_depth)
    except Exception as e:
        console.print_exception(show_locals=True)
        if retry2_depth > retry2:
            try:
                raise Exception(f"Retry times exceeded: {retry2_depth}")
            except:
                console.print_exception(show_locals=True)
        else:
            return await Voice_Change_Batch_V2(Voice_pth, index_path, 
                                        wav_dir_path, 
                                        PitchExtraction=PitchExtraction,
                                        do_change_voice=do_change_voice,
                                        await_opt=await_opt,
                                        a=a,
                                        retry_times=retry_times,
                                        retry_depth=retry_depth+1,
                                        retry2=retry2,
                                        retry2_depth=retry2_depth)

app = fastapi.FastAPI()
@app.get("/get/list/{TYPE_}")
async def redirect_to_(TYPE_):
    return fastapi.responses.RedirectResponse(url=f"/get/list/{TYPE_}/full_path")

@app.get("/get/list/{TYPE_}/full_path")
async def get_list(TYPE_: str):
    if TYPE_ not in ["voice_pth", "voice_index"]:
        raise fastapi.HTTPException(status_code=400, 
                                    detail="Invalid TYPE_, the TYPE_ should be \"voice_pth\" or \"voice_index\"")
    else:
        if TYPE_ == "voice_pth":
            return {"files_": list(get_all_file(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_pth"), "pth"))}
        elif TYPE_ == "voice_index":
            return {"files_": list(get_all_file(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_index"), "index"))}

@app.get("/get/list/{TYPE_}/name")
async def get_list_name(TYPE_: str):
    if TYPE_ not in ["voice_pth", "voice_index"]:
        raise fastapi.HTTPException(status_code=400, 
                                    detail="Invalid TYPE_, the TYPE_ should be \"voice_pth\" or \"voice_index\"")
    else:
        if TYPE_ == "voice_pth":
            return {"files_": list(get_all_file_name(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_pth"), "pth"))}
        elif TYPE_ == "voice_index":
            return {"files_": list(get_all_file_name(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_index"), "index"))}

@app.post("/upload/voice/pth")
async def upload_voice(files: list[fastapi.UploadFile] = fastapi.File(...)):
    VoicePthPath = str(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_pth"))
    if not os.path.exists(VoicePthPath):
        fl.create_dir(Path(VoicePthPath))
    for file in files:
        if not file.filename.endswith(".pth"):
            continue
        with open(str(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_pth",file.filename)), "wb") as f:
            f.write(await file.read())
    return {"message": "Files uploaded successfully"}

@app.post("/upload/voice/index")
async def upload_index(files: list[fastapi.UploadFile] = fastapi.File(...)):
    IndexPath = str(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_index"))
    if not os.path.exists(IndexPath):
        fl.create_dir(Path(IndexPath))
    for file in files:
        if not file.filename.endswith(".index"):
            continue
        with open(str(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_index",file.filename)), "wb") as f:
            f.write(await file.read())
    return {"message": "Files uploaded successfully"}

@app.post("/change/{voice_name}/{voice_index}/single")
async def change_voice_single(voice_name: str,
                            voice_index: str,
                            background_tasks: BackgroundTasks,
                            files: list[fastapi.UploadFile] = fastapi.File(...)):
    if len(files) != 1:
        raise fastapi.HTTPException(status_code=400, detail="Exactly one file must be uploaded")
    file = files[0]
    if not file.filename.endswith(".wav"):
        raise fastapi.HTTPException(status_code=400, detail="File must be a .wav file")
    wav_path = str(fl.merge_dir_txt2(TEMP_DIR, f"VoiceChange_Request_{uuid.uuid4()}.wav"))
    with open(wav_path, "wb") as f:
        f.write(await file.read())
    data = await Voice_Change(get_pth(voice_name)[1], 
                            get_index(voice_index)[1], 
                            wav_path, 
                            PitchExtraction="pm")
    background_tasks.add_task(fl.delete_file, Path(wav_path))
    opt = data["data"]
    return fastapi.responses.Response(content=opt, media_type="audio/wav")

@app.post("/change/{voice_name}/{voice_index}/batch")
async def change_voice_batch(voice_name: str,
                             voice_index: str,
                             background_tasks: BackgroundTasks,
                             files: list[fastapi.UploadFile] = fastapi.File(...)):
    if not voice_name.endswith(".pth"):
        voice_name += ".pth"
    
    await change_voice_pth(str(fl.merge_dir_txt2(LOCAL_STORAGE_DIR,"Voice_pth",f"{voice_name}")))
    index_path = get_index(f"{voice_index}")[1]
    Temp_Wav = str(fl.merge_dir_txt2(TEMP_DIR, f"VoiceChange_Request_{uuid.uuid4()}"))
    fl.create_dir(Path(Temp_Wav))
    for file in files:
        with open(str(fl.merge_dir_txt2(Temp_Wav,file.filename)), "wb") as f:
            f.write(await file.read())
    output = await Voice_Change_Batch_V2(voice_name, 
                                      index_path, 
                                      Temp_Wav, 
                                      PitchExtraction="pm",
                                      do_change_voice=False)
    output = output["output_dir"] 
    fd, f_name = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    with zipfile.ZipFile(f_name, 'w') as zipf:
        for f in os.listdir(output):
            zipf.write(os.path.join(output, f), f)
    background_tasks.add_task(fl.delete_file, Path(f_name))
    return FileResponse(f_name, media_type="application/zip", filename="archive.zip")
    

if __name__ == "__main__":
    Clear_Weights_Trash()
    Clear_Index_Trash()
    Update_Injection_weights()
    uvicorn.run("api:app", 
                host="0.0.0.0", 
                port=14514,
                reload=True)