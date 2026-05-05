from . import file__lib as fl
from . import multi_thread_web_downloader as mtwd
from . import file_search as fs
from . import easy_7zip as e7z
from . import log_lib
from . import cmd_downloader

import json
from pathlib import Path

LOGGER = log_lib.LogStream("build", fl.merge_dir_txt2(fl.get_my_dir(), "Log",), log_lib.DEBUG, f_display=True).logger
URL_DEFAULT = 'https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/RVC1006Nvidia.7z'
ROOT_DIR = fl.get_my_dir()
TEMP_DIR = fl.merge_dir_txt(ROOT_DIR, 'Temp')
THIRD_PARTY_DIR = fl.merge_dir_txt(ROOT_DIR, 'ThirdParty')
LOG_DIR = fl.merge_dir_txt(ROOT_DIR, 'Log')
CONFIG_DIR = fl.merge_dir_txt(ROOT_DIR, 'Config')

with open(str(fl.merge_dir_txt(CONFIG_DIR, 'Main.json')), 'r') as f:
    CONFIG = json.load(f)
with open(str(fl.merge_dir_txt(CONFIG_DIR, 'GPU_Platforms.json')), 'r') as f:
    GPU_PLATFORMS = json.load(f)

Using_GPU_Platform_Installation_Sources = CONFIG.get("Using_GPU_Platform_Installation_Sources", True)
GPU_Platform = CONFIG.get("GPU_Platform", "Nvidia")
if Using_GPU_Platform_Installation_Sources:
    URL = GPU_PLATFORMS.get(GPU_Platform, URL_DEFAULT)
else:
    URL = URL_DEFAULT

Using_ZH_CN_Quick_Installation_Sources = CONFIG.get("Using_ZH_CN_Quick_Installation_Sources", False)
Source = CONFIG.get("Source", "HF_Mirror_Nvidia")
if Using_ZH_CN_Quick_Installation_Sources:
    URL = GPU_PLATFORMS.get(Source, URL)
else:
    URL = URL


def download_file(url, save_path):
    try:
        LOGGER.info(f"开始下载：{url}")
        LOGGER.info(f"保存路径：{save_path}")
        
        # downloder = mtwd.MultiThreadDownloader(url, save_path, 10, 30)
        # downloder.download()
        cmd_downloader.download(url, save_path, timeout=30)
        LOGGER.info(f"下载完成：{save_path}")
    except Exception as e:
        LOGGER.error(f"下载失败：{e}")
        return False
    return True

def check_installed(path):
    res = fs.search_file_by_name(path, 'ffmpeg.exe')
    if len(res) > 0:
        return True, res[0].store_location
    return False,None

def extract_file(file_path, extract_path):
    LOGGER.info(f"Start extract: {file_path} -> {extract_path}")
    if not e7z.check_installed(e7z._7zip_path):
        e7z._7zip_install(e7z._7zip_path)
    return e7z.extract(file_path, extract_path, e7z._7zip_path)

def install_RVC():
    if not fl.file_exists(THIRD_PARTY_DIR):
        LOGGER.warning(f"ThirdParty dir not exists, create it: {THIRD_PARTY_DIR}")
    res = check_installed(THIRD_PARTY_DIR)
    if res[0]:
        LOGGER.info(f"RVC already installed: {res[1]}")
        return res[1]
    if not fl.file_exists(TEMP_DIR):
        LOGGER.warning(f"Temp dir not exists, create it: {TEMP_DIR}")
        fl.create_dir(TEMP_DIR)
    file_path = fl.merge_dir_txt(TEMP_DIR, 'RVC.7z')
    LOGGER.info(f"Downloading RVC -> {file_path}")
    if not fl.file_exists(Path(file_path)):
        res = download_file(URL, file_path)
        if not res:
            LOGGER.error(f"Download failed: {file_path}")
            raise RuntimeError("Download failed")
        else:
            LOGGER.info(f"Download complete: {file_path}")
    extract_path = fl.merge_dir_txt(THIRD_PARTY_DIR, 'RVC')
    if not fl.file_exists(Path(extract_path)):
        extract_file(file_path, extract_path)
        LOGGER.info(f"Extract complete: {extract_path}")
        fl.delete_file(Path(file_path))
    
    return extract_path
def main():
    LOGGER.info("Start build")
    inst_location = install_RVC()
    LOGGER.debug(f"RVC installed at: {inst_location}")
    root_location = fs.search_file_by_name(inst_location, 'ffmpeg.exe')[0].store_location
    LOGGER.debug(f"Root location: {root_location}")

    print(f"<install_location>{inst_location}</install_location>")
    print(f"<root_location>{root_location}</root_location>")
    return inst_location, root_location
if __name__ == '__main__':
    print("MadArtist VoiceChange Server Build Script - Version Alpha_0.0.1_202605")
    main()

