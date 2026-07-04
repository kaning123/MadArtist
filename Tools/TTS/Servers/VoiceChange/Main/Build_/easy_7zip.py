from . import cmd_downloader
import subprocess
from . import file__lib as fl
from pathlib import Path
from .silence_installer import silence_install_exe
from . import log_lib

_7ZIP_URL = "https://www.7-zip.org/a/7z{ver_without_dot}-x64.exe"
_7zip_path = fl.merge_dir_txt2(fl.get_my_dir(), "ThirdParty", "7zip")

logger = log_lib.LogStream("easy_7zip", fl.merge_dir_txt2(fl.get_my_dir(),"Log",),
                           log_lib.DEBUG, f_display=True).logger
def download_file(url: str, dest_path: Path,timeout=100):
    logger.info(f"Downloading {url} to {dest_path}...")
    logger.debug(f"Timeout set to {timeout} seconds.")
    if not Path(dest_path).exists():
        cmd_downloader.download(url, str(dest_path), timeout=timeout)
    return dest_path
def _7zip_install(_7zip_path: Path,ver="25.01"):
    ver_without_dot = ver.replace(".", "")
    logger.debug("Installing 7zip version {ver} at {_7zip_path}")
    try:
        logger.info(f"Checking if 7zip is already installed at {_7zip_path}")
        open(fl.merge_dir_txt(_7zip_path, "INSTALLED"))
    except FileNotFoundError:
        logger.error(f"7zip not found at {_7zip_path}.")
        logger.info(f"installing 7zip version {ver}...")

        _7zinst = fl.merge_dir_txt2(fl.get_my_dir(),'Temp','7zinst.exe')
        _7zurl = _7ZIP_URL.format(ver=ver,ver_without_dot=ver_without_dot)
        if not _7zinst.exists():
            logger.info(f"Downloading 7zip version {ver} from {_7zurl} to {_7zinst}...")
            _7zip_zip_path = download_file(_7zurl, _7zinst)
        else:
            _7zip_zip_path = _7zinst
        logger.info(f"Installing 7zip version {ver} from {_7zip_zip_path} to {_7zip_path}...")
        silence_install_exe(_7zip_zip_path, _7zip_path)
        fl.create_dir(_7zip_path)
        logger.info(f"7zip version {ver} installed at {_7zip_path}.")
        with open(fl.merge_dir_txt(_7zip_path, "INSTALLED"), "x") as f:
            f.write(f"7zip version {ver} installed.")
        fl.delete_file(_7zip_zip_path)
    return _7zip_path

def get_7zip_exe_path(_7zip_path: Path):
    logger.debug(f"Getting 7zip.exe path from {_7zip_path}")
    if not fl.file_exists(fl.merge_dir_txt(_7zip_path, "7z.exe")):
        logger.debug('INSTALLED :', fl.merge_dir_txt(_7zip_path, "INSTALLED"))
        fl.delete_file(fl.merge_dir_txt(_7zip_path, "INSTALLED"))    #删除INSTALLED文件
        _7zip_path = _7zip_install(_7zip_path)
    return fl.merge_dir_txt(_7zip_path, "7z.exe")
def extract(file_path: Path, dest_path: Path, _7zip_path: Path):
    _7zip_exe_path = get_7zip_exe_path(_7zip_path)
    if not fl.file_exists(_7zip_exe_path):
        logger.error(f"7zip not found at {_7zip_path}.")
        _7zip_install(_7zip_path)
    if not fl.file_exists(file_path):
        logger.error(f"{file_path} not found.")
        raise FileNotFoundError(f"{file_path} not found.")
    if not fl.file_exists(dest_path):
        fl.create_dir(dest_path)
    command = [str(_7zip_exe_path), 'x', str(file_path), f"-o{str(dest_path)}"]
    subprocess.run(command, check=True)
    return dest_path
def check_installed(_7zip_path: Path):
    return fl.file_exists(fl.merge_dir_txt(_7zip_path, "INSTALLED"))
def uninstall_7zip(_7zip_path: Path):
    fl.delete_dir(_7zip_path)
if __name__ == "__main__":
    
    _7zip_install(_7zip_path)
    print(get_7zip_exe_path(_7zip_path))
