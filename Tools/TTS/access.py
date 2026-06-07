import fastapi
import os
import shutil
from pathlib import Path
import json
import requests
import asyncio
import uuid
import file_lib as fl
import traceback

def get_my_dir():
    return os.path.dirname(os.path.abspath(__file__))

def get_parent_dir(dir_path,depth=1):
    parent_path = Path(dir_path)
    for _ in range(depth):
        parent_path = parent_path.parent
    return parent_path

def merge_dir_txt(a,b):
    c=os.path.join(a,b)
    return c
def merge_dir_txt2(*TXT):
    return Path(os.path.join(*TXT))
def create_dir(path: Path, overwrite=False) -> bool:
    if overwrite and path.exists():
        shutil.rmtree(path)
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path.exists()
def get_dir_children_dirs(path: Path):
    return [item for item in path.iterdir() if item.is_dir()]
def get_dir_children_files(path: Path):
    return [item for item in path.iterdir() if item.is_file()]
def delete_dir(path: Path):
    return shutil.rmtree(path)
def delete_file(path: Path):
    return os.remove(path)
def file_exists(path: Path):
    path = Path(path)
    return path.exists()

STORAGE_DIR = merge_dir_txt2(get_my_dir(), "Storage")
if not STORAGE_DIR.exists():
    create_dir(STORAGE_DIR)

CONFIG_DIR = merge_dir_txt2(STORAGE_DIR, "Config")
if not CONFIG_DIR.exists():
    create_dir(CONFIG_DIR)

with open(os.path.join(CONFIG_DIR, "ServConfig.json")) as f:
    config = json.load(f)

BaseGeneratorURL = config["BaseGeneratorURL"]
VoiceChange_URL = config["VoiceChange_URL"]
app = fastapi.FastAPI()



@app.get("/get/list/BaseVoiceGenerator")
async def get_base_voice_generator_list():
    try:
        response = requests.get(f"{BaseGeneratorURL}/list/voices")
        return response.json()
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.get("/get/list/VoiceChanger/Voice")
async def get_voice_changer_voice_list():
    try:
        response = requests.get(f"{VoiceChange_URL}/get/list/voice_pth")
        return response.json()
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.get("/get/list/VoiceChanger/Index")
async def get_voice_changer_index_list():
    try:
        response = requests.get(f"{VoiceChange_URL}/get/list/voice_index")
        return response.json()
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.get("/get/list/VoiceChanger/{type_}/name")
async def get_voice_changer_voice_list_by_type(type_):
    try:
        response = requests.get(f"{VoiceChange_URL}/get/list/{type_}/name")
        return response.json()
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.get("/get/wav/BaseVoiceGenerator/{voice_name}/{text}")
async def get_base_voice_generator_wav(voice_name,text):
    try:
        response = requests.get(f"{BaseGeneratorURL}/generate/{voice_name}/{text}")
        return fastapi.responses.Response(content=response.content, media_type="audio/wav")
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.post("/get/wav/VoiceChanger/{voice_name}")
async def get_voice_changer_wav(voice_name,wav_path):
    try:
        response = requests.post(f"{VoiceChange_URL}/change/{voice_name}", files={"file": open(wav_path, "rb")})
        return fastapi.responses.Response(content=response.content, media_type="audio/wav")
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.post("/upload/voice")
async def upload_voice(files: list[fastapi.UploadFile] = fastapi.File(...)):
    try:
        files_ = fl.process_fastapi_uploadfile_list(files)
        response = requests.post(f"{VoiceChange_URL}/upload/voice/pth", 
                                 files=files_)
        return response.json()
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))

@app.post("/upload/index")
async def upload_index(files: list[fastapi.UploadFile] = fastapi.File(...)):
    try:
        files_ = fl.process_fastapi_uploadfile_list(files)
        response = requests.post(f"{VoiceChange_URL}/upload/voice/index", 
                                 files=files_)
        return response.json()
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=str(e))
    
@app.post("/change/voice/{type_}/{voice_name}/{voice_index}")
async def change_voice(type_,voice_name,voice_index,files: list[fastapi.UploadFile] = fastapi.File(...)):
    try:
        files_ = fl.process_fastapi_uploadfile_list(files)
        response = requests.post(f"{VoiceChange_URL}/change/{voice_name}/{voice_index}/{type_}",
                                 files=files_)
        return fastapi.Response(content=response.content, media_type="application/zip")
    except Exception as e:
        traceback.print_exc() # Print the traceback for debugging
        raise fastapi.HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("access:app", 
                host="0.0.0.0",
                port=8848,
                reload=True)