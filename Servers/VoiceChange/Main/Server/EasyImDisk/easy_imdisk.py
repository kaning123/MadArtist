import sys
from . import file_lib as fl
from . import cmd_downloader
from .log_lib import LogStream as LS
from . import log_lib
from pathlib import Path
from . import easy_7zip as ez7
import subprocess
from . import run_as_lib
from . import format_lib   
import os
import sys
import time
sys.path.pop()

IMDISK_DEFAULT_PATH = fl.merge_dir_txt2(fl.get_my_dir(), "ThirdParty", "ImDisk")
IMDISK_URL = "https://sf-west-interserver-1.dl.sourceforge.net/project/imdisk-toolkit/20250206/ImDiskTk-x64.zip?viasf=1"
TEMP_DIR = fl.merge_dir_txt2(fl.get_my_dir(),"Temp")
LOG_DIR = fl.merge_dir_txt2(fl.get_my_dir(),"Log",)
if not os.path.exists(LOG_DIR):
    fl.create_dir(LOG_DIR)
if not os.path.exists(TEMP_DIR):
    fl.create_dir(TEMP_DIR)
logger = LS("easy_imdisk", LOG_DIR, log_lib.DEBUG, f_display=True).logger
imdisk_path = fl.merge_dir_txt2(fl.get_my_dir(), "ThirdParty", "ImDisk")


class ImDiskError(Exception):
    pass
def download_file(url, file_path, chunk_size=1024*1024, timeout=100):
    try:
        cmd_downloader.download(url, file_path, chunk_size, timeout)
        return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False

def get_imdisk_unit(drive_letter: str) -> str:
    """根据盘符获取ImDisk设备编号（如0、1），用于强制卸载"""
    list_cmd = ['imdisk', '-l', '-n']  # -n 只显示设备编号
    result = subprocess.run(
        list_cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to list ImDisk units: {result.stderr}")
    
    # 解析输出，匹配盘符对应的设备编号
    for line in result.stdout.splitlines():
        if drive_letter.upper() in line:
            return line.split()[0]  # 提取设备编号（如0）
    raise RuntimeError(f"No ImDisk unit found for {drive_letter}")

def format_disk(drive_letter,FS="NTFS",quick=True,*AdditionInfo,**AdditionParams):
    #hint: only ntfs is supported for now.
    try:
        logger.info(f"Formatting {drive_letter} as {FS}")
        command_format = ['format', drive_letter, f'/FS:{FS}']
        if quick:
            command_format.append('/Q')
        command_format.append('/Y')
        format_lib.main(drive_letter,_await=2)
        if False:
            run_as_lib.run(command_format,*AdditionInfo,**AdditionParams)
        logger.info(f"Formatted {drive_letter} as {FS}")
        return True
    except Exception as e:
        logger.error(f"Error formatting disk: {e}")
        return False
def imdisk_install(imdisk_path: Path):
    try:
        if not fl.merge_dir_txt2(imdisk_path,"INSTALLED").exists():
            logger.info(f"Installing ImDisk to {imdisk_path}")
            imdisk_zip_path = fl.merge_dir_txt2(TEMP_DIR, "ImDiskTk-x64.zip")
            if not imdisk_zip_path.exists():
                if not download_file(IMDISK_URL, imdisk_zip_path):
                    logger.error("Failed to download ImDisk.")
                    return False
            _7z_exe = ez7.get_7zip_exe_path(fl.merge_dir_txt2(fl.get_my_dir(), "ThirdParty", "7zip"))
            if not _7z_exe:
                logger.error("Failed to find 7zip.exe.")
                ez7._7zip_install(fl.merge_dir_txt2(fl.get_my_dir(), "ThirdParty", "7zip"))
                _7z_exe = ez7.get_7zip_exe_path(fl.merge_dir_txt2(fl.get_my_dir(), "ThirdParty", "7zip"))
            ez7.extract(imdisk_zip_path, TEMP_DIR, Path(_7z_exe).parent)
            fl.delete_file(imdisk_zip_path)
            installation_bat_path = fl.merge_dir_txt2(TEMP_DIR,'ImDiskTk20250206',"install.bat")
            #subprocess.run([str(installation_bat_path),"help"], check=True)
            with open(fl.merge_dir_txt2(fl.get_my_dir(),'install.txt'),'r') as f:
                ovrd = f.read()
            with open(fl.merge_dir_txt2(TEMP_DIR,'ImDiskTk20250206',"install.bat"),'w') as f:
                f.write(ovrd)
            command_install = [str(installation_bat_path), "/silent",f"/installfolder:{str(imdisk_path)}","/menu_entries:0","/shortcuts_desktop:0",'/discutils:1','/ramdiskui:1','/shortcuts_all:0']
            subprocess.run(command_install, check=True)
            logger.info(f"ImDisk installed at {imdisk_path}")
            fl.create_dir(imdisk_path)
            with open(fl.merge_dir_txt(imdisk_path,"INSTALLED"),"x") as f:
                f.write("ImDisk installed.")
            fl.delete_dir(fl.merge_dir_txt2(TEMP_DIR,'ImDiskTk20250206'))
            return True
        else:
            logger.info(f"ImDisk is already installed at {imdisk_path}")
            return True
    except Exception as e:
        logger.error(f"Error installing ImDisk: {e}")
        return False

def uninst_imdisk(imdisk_path: Path):
    try:
        logger.info(f"Uninstalling ImDisk from {imdisk_path}")
        uninst_exe = fl.merge_dir_txt2(imdisk_path,"config.exe")
        command_uninstall = [str(uninst_exe), "/silentuninstall"]
        subprocess.run(command_uninstall, check=True)
        logger.info(f"ImDisk uninstalled from {imdisk_path}")
        logger.debug(f"Deleting INSTALLED")
        fl.delete_file(fl.merge_dir_txt(imdisk_path,"INSTALLED"))
    except Exception as e:
        logger.error(f"Error uninstalling ImDisk: {e}")
    finally:
        if fl.file_exists(fl.merge_dir_txt(imdisk_path,"INSTALLED")):
            fl.delete_file(fl.merge_dir_txt(imdisk_path,"INSTALLED"))

def check_imdisk_installed(imdisk_store_path: Path):
    check_cmd = ['imdisk', '--version']
    try:
        result = subprocess.run(check_cmd, capture_output=True, text=True, check=True)
        logger.info(f"ImDisk is installed: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"ImDisk is not installed or not found: {e}")
        return False
    
def _check(imdisk_store_path: Path):
    if not check_imdisk_installed(imdisk_store_path):
        installed = imdisk_install(imdisk_store_path)
        if not installed:
            logger.error("Failed to install ImDisk. Cannot create RAM disk.")
            raise ImDiskError("ImDisk error! Failed to install ImDisk. Cannot create RAM disk.")
        
def mount_image(image_path,drive_letter,imdisk_store_path,*AdditionInfo):
    try:
        _check(imdisk_store_path)
        logger.info(f"Mounting {image_path} to {drive_letter}")
        command_mount = ['imdisk', 
                            '-a', 
                            '-t', 'file',
                            '-m', drive_letter,
                            '-f', str(image_path),
                            *AdditionInfo]
        subprocess.run(command_mount, check=True)
        logger.info(f"Image mounted to {drive_letter}")
        return True
    except Exception as e:
        logger.error(f"Error mounting image: {e}")
        return False
def make_ram_disk(size_mb:int,drive_letter:str,imdisk_store_path: Path,FS:str="NTFS",*AdditionInfo):

    try:
        _check(imdisk_store_path)
        logger.info(f"Creating RAM disk of size {size_mb} MB at {drive_letter}")
        command_ramdisk = ['imdisk',
                            '-a',
                            '-t', 'vm',
                            '-m', drive_letter,
                            '-s', f'{size_mb}M',
                            #'-p', f'/fs:{FS} /q /y',
                            *AdditionInfo]
        logger.debug(f"RAM disk command: {command_ramdisk}")
        run_as_lib.run(command_ramdisk)
        logger.info(f"RAM disk created at {drive_letter}")
        logger.info(f"Formatting RAM disk {drive_letter} as {FS}")
        format_disk(drive_letter,FS=FS,quick=True)
        logger.info(f"RAM disk formatted as {FS}")
        return True
    except Exception as e:
        logger.error(f"Error creating RAM disk: {e}")
        return False
    
def unmount_disk(drive_letter,imdisk_store_path,*AdditionInfo):
    try:
        _check(imdisk_store_path)
        logger.info(f"Unmounting {drive_letter}")
        command_unmount = ['imdisk',
                            '-d',
                            '-m', drive_letter,
                            *AdditionInfo]
        subprocess.run(command_unmount, check=True)
        logger.info(f"Image unmounted from {drive_letter}")
        return True
    except Exception as e:
        logger.error(f"Error unmounting image: {e}")
        return False
    
def unmount_disk_forceA(drive_letter,imdisk_store_path,*AdditionInfo):
    try:
        _check(imdisk_store_path)
        logger.info(f"Force unmounting {drive_letter}")
        command_unmount = ['imdisk',
                            '-D',
                            '-m', drive_letter,
                            *AdditionInfo]
        subprocess.run(command_unmount, check=True)
        logger.info(f"Image force unmounted from {drive_letter}")
        return True
    except Exception as e:
        logger.error(f"Error force unmounting image: {e}")
        return False
    
def unmount_disk_forceB(drive_letter,imdisk_store_path,*AdditionInfo):
    try:
        _check(imdisk_store_path)
        unit = get_imdisk_unit(drive_letter)
        logger.info(f"Force unmounting ImDisk unit {unit} for {drive_letter}")
        logger.info(f"Force unmounting {drive_letter}")
        command_unmount = ['imdisk',
                           '-R',
                           '-u', unit,
                           *AdditionInfo]
        subprocess.run(command_unmount, check=True)
        logger.info(f"Image force unmounted from {drive_letter}")
        return True
    except Exception as e:
        logger.error(f"Error force unmounting image: {e}")
        return False
    
class MountedImage:
    def __init__(self,file_path,drive_letter,imdisk_store_path) -> None:
        try:
            _check(imdisk_store_path)
            self.file_path = file_path
            self.drive_letter = drive_letter
            self.imdisk_store_path = imdisk_store_path
            self.mounted = False
        except ImDiskError as e:
            logger.error(f"Error initializing MountedImage: {e}")
            raise
    def mount(self,*AdditionInfo):
        if not self.mounted:
            success = mount_image(self.file_path, self.drive_letter, self.imdisk_store_path, *AdditionInfo)
            if success:
                self.mounted = True
            else:
                raise ImDiskError("Failed to mount image.")
    def unmount(self,*AdditionInfo):
        if self.mounted:
            success = unmount_disk(self.drive_letter, self.imdisk_store_path, *AdditionInfo)
            if success:
                self.mounted = False
            else:
                raise ImDiskError("Failed to unmount image.")
    def unmount_forceA(self,*AdditionInfo):
        if self.mounted:
            success = unmount_disk_forceA(self.drive_letter, self.imdisk_store_path, *AdditionInfo)
            if success:
                self.mounted = False
            else:
                raise ImDiskError("Failed to force unmount image.")
    def unmount_forceB(self,*AdditionInfo):
        if self.mounted:
            success = unmount_disk_forceB(self.drive_letter, self.imdisk_store_path, *AdditionInfo)
            if success:
                self.mounted = False
            else:
                raise ImDiskError("Failed to force unmount image.")
    def __enter__(self):
        self.mount()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.unmount()
        except ImDiskError:
            try:
                self.unmount_forceA()
            except ImDiskError:
                self.unmount_forceB()
    def __str__(self):
        return self.drive_letter

class RamDisk:
    def __init__(self,size_mb:int,drive_letter:str,imdisk_store_path: Path,FS:str="NTFS") -> None:
        if not drive_letter.endswith(":"):
            drive_letter += ":"
        try:
            _check(imdisk_store_path)
            self.size_mb = size_mb
            self.drive_letter = drive_letter
            self.imdisk_store_path = imdisk_store_path
            self.FS = FS
            self.created = False
        except ImDiskError as e:
            logger.error(f"Error initializing RamDisk: {e}")
            raise
    def create(self,*AdditionInfo):
        if not self.created:
            success = make_ram_disk(self.size_mb, self.drive_letter, self.imdisk_store_path, self.FS, *AdditionInfo)
            if success:
                self.created = True
            else:
                raise ImDiskError("Failed to create RAM disk.")
    def delete(self,*AdditionInfo):
        if self.created:
            success = unmount_disk(self.drive_letter, self.imdisk_store_path, *AdditionInfo)
            if success:
                self.created = False
            else:
                raise ImDiskError("Failed to delete RAM disk.")
    def forceA_delete(self,*AdditionInfo):
        if self.created:
            success = unmount_disk_forceA(self.drive_letter, self.imdisk_store_path, *AdditionInfo)
            if success:
                self.created = False
            else:
                raise ImDiskError("Failed to force delete RAM disk.")
    def forceB_delete(self,*AdditionInfo):
        if self.created:
            success = unmount_disk_forceB(self.drive_letter, self.imdisk_store_path, *AdditionInfo)
            if success:
                self.created = False
            else:
                raise ImDiskError("Failed to force delete RAM disk.")
    def __enter__(self):
        self.create()
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.delete()
        except ImDiskError:
            try:
                self.forceA_delete()
            except ImDiskError:
                self.forceB_delete()

    def __str__(self):
        return self.drive_letter
if __name__ == "__main__":
    #imdisk_path = fl.merge_dir_txt2(fl.get_my_dir(), "ThirdParty", "ImDisk")
    with RamDisk(5120, "R", imdisk_path, "NTFS") as ram_disk:
        ram_disk.create()

    


