import easy_7zip,requests
import cmd_downloader
import subprocess
from pathlib import Path
import file_lib as fl
import json
from silence_installer import silence_install_exe

CONFIG_DIR = fl.merge_dir_txt2(fl.get_my_dir(), "Config")
CONFIGS_DIR = fl.merge_dir_txt2(str(Path(fl.get_my_dir()).parent), "Configs")

with open(str(fl.merge_dir_txt2(CONFIG_DIR, "URL.json")), "r") as f:
    URL_CONFIG = json.load(f)
with open(str(fl.merge_dir_txt2(CONFIGS_DIR, "EasyFFmpegConfig.json")), "r") as f:
    EASY_FFMPEG_CONFIG = json.load(f)

FFMPEG_URL = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip'
FFMPEG_CHECK_SUM_URL = 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/checksums.sha256'

USING_SOURCE = EASY_FFMPEG_CONFIG['UsingSource']
for i in URL_CONFIG:
    if i['Name'] == USING_SOURCE:
        FFMPEG_URL = i["URLs"]["DownloadFile"]
        FFMPEG_CHECK_SUM_URL = i["URLs"]["CheckSum"]
        break

def download_file(url: str, dest_path: Path):
    if not Path(dest_path).exists():
        cmd_downloader.download(url, str(dest_path), timeout=100)
    return dest_path
 
def ffmpeg_install(ffmpeg_path: Path):
    try:
        open(fl.merge_dir_txt(ffmpeg_path, "INSTALLED"))
    except FileNotFoundError:
        ffmpeg_zip = fl.merge_dir_txt2(fl.get_my_dir(),'Temp','ffmpeg.zip')
        ffmpeg_zip_path = download_file(FFMPEG_URL, ffmpeg_zip)
        _7z_exe = easy_7zip.get_7zip_exe_path(fl.merge_dir_txt2(fl.get_my_dir(), "ThirdParty", "7zip"))
        easy_7zip.extract(ffmpeg_zip_path, ffmpeg_path, Path(_7z_exe).parent)
        fl.delete_file(ffmpeg_zip_path)

if __name__ == "__main__":
    ffmpeg_path = fl.merge_dir_txt2(fl.get_my_dir(), "ThirdParty", "FFmpeg")
    ffmpeg_install(ffmpeg_path)

