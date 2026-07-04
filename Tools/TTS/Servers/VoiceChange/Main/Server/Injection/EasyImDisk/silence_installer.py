import subprocess
from pathlib import Path
from . import log_lib
from . import UAC_lib as uac
from . import file_lib as fl
LOG_DIR = fl.merge_dir_txt2(fl.get_my_dir(),"Log")

def silence_install_exe(FilePath:Path,DistPath:Path):
    """静默安装"""

    logger = log_lib.LogStream("silence_installer", LOG_DIR, log_lib.DEBUG, f_display=True).logger
    try:
        logger.info(f"开始静默安装 {FilePath} 到 {DistPath}")
        command = ['powershell',str(FilePath),'/S','/D='+str(DistPath)]
        logger.debug(f"静默安装命令：{command}")
        subprocess.run(command, shell=True, check=True)
        logger.info(f"静默安装 {FilePath} 到 {DistPath} 完成")
    except Exception as e:
        logger.error(f"静默安装 {FilePath} 到 {DistPath} 失败：{e}")