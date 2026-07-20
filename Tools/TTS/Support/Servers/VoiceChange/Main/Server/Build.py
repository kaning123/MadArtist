print("MadArtist Server Build - Version Alpha_0.0.1_202606")

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
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click]),]
)
logger_ = logging.getLogger(__name__)

import os
from pathlib import Path
import file_lib as fl
import json
import time
import shutil
import traceback
import subprocess

ROOT_DIR = str(Path(fl.get_my_dir()).parent)
BUILD__DIR = fl.merge_dir_txt(ROOT_DIR, 'Build_')
CONFIG_DIR = fl.merge_dir_txt(ROOT_DIR, 'Config')
INJECTION_DIR = fl.merge_dir_txt2(ROOT_DIR, 'Server', 'Injection')
INJECTION2_DIR = fl.merge_dir_txt2(ROOT_DIR, 'Server', 'Injection2')
RVC_PIP_PACKAGE_INJECTION = fl.merge_dir_txt2(ROOT_DIR, 'Server', "RVC_pip_package_Injecion")

import sys
#print(sys.path)
sys.path.append(ROOT_DIR)
try:
    import Build_.build as build
    import Build_.log_lib as log_lib
except:
    traceback.print_exc()
finally:
    del sys.path[-1]

from pathlib import Path

logger = log_lib.get_logger("Build", 
                            fl.merge_dir_txt(BUILD__DIR, "Log"), 
                            log_lib.DEBUG,
                            c_display=False, 
                            f_display=True).logger
class MadPath:
    def parse_list(self,l:list[str]):
        for i in range(len(l)):
            if l[i].startswith("~~##") and l[i].endswith("##~~"):
                l[i] = self.env[l[i].replace("~~##", "").replace("##~~", "")]
        return l
    def __init__(self, l:list, root:list,env:dict):
        logger_.info(f"MadPath initialized with l: {l} and root: {root}")
        logger_.info(f"MadPath initialized with env: {env}")
        self.env = env
        self.root = self.parse_list(root)
        self.l = self.parse_list(l)
        self.path = fl.merge_dir_txt2(*self.root,*self.l)
    def __str__(self) -> str:
        return str(self.path)

def Build():
    res = build.main()
    for i in INJECTION_DIR.iterdir():
        if i.is_file():
            shutil.copy2(str(i), str(res[1]))
        elif i.is_dir():
            shutil.copytree(str(i), str(fl.merge_dir_txt2(res[1], i.name)), dirs_exist_ok=True)
    try:
        with open(fl.merge_dir_txt(INJECTION2_DIR, "inject.json"), "r") as f:
            injected = json.load(f)
    except:
        traceback.print_exc()
        sys.exit(1)
    RVC_ROOT = res[1]
    RVC_RUNTIME = fl.merge_dir_txt2(RVC_ROOT, 'Runtime',"python.exe")
    for i in injected["Injections"]:
        file_path = str(MadPath([i["target"]],
                            i["root"],
                            globals()))
        dest_path = str(MadPath([i["injection"]],
                            i["destination"],
                            globals()))
        logger.info(f"Injecting {file_path} to {dest_path}")
        shutil.copy2(file_path, dest_path)
    json_write = {"Build_Time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),"install_location": str(res[0]), "root_location": str(res[1])}
    with open(fl.merge_dir_txt(CONFIG_DIR, 'Build.json'), 'w') as f:
        json.dump(json_write, f)
    with open(fl.merge_dir_txt(BUILD__DIR, 'install.json'), 'w') as f:
        json.dump(json_write, f)

    CMD_BASE = [f"{RVC_RUNTIME}",
           "-m",
           "pip",
           "install",
           ]
    logger.info("Updating pip")
    subprocess.run([*CMD_BASE, "--upgrade", "pip"], check=True)
    logger.info("Installing pip requirements")
    for f in os.listdir(RVC_PIP_PACKAGE_INJECTION):
        if f.endswith(".txt"):
            req_file = fl.merge_dir_txt2(RVC_PIP_PACKAGE_INJECTION, f)
            logger.info(f"Installing pip requirements from {req_file}")
            cmd = [*CMD_BASE,
                   "-r",
                   str(req_file)]
            subprocess.run(cmd, check=True)
    logger.info("fixing setuptools issue")
    subprocess.run([*CMD_BASE, 
                    "setuptools<82.0.0",
                    "--force-reinstall"], check=True) # RVC can't work with setuptools>=82.0.0
if __name__ == '__main__':
    res = build.main()
    for i in INJECTION_DIR.iterdir():
        if i.is_file():
            shutil.copy2(str(i), str(res[1]))
        elif i.is_dir():
            shutil.copytree(str(i), str(fl.merge_dir_txt2(res[1], i.name)), dirs_exist_ok=True)
    try:
        with open(fl.merge_dir_txt(INJECTION2_DIR, "inject.json"), "r") as f:
            injected = json.load(f)
    except:
        traceback.print_exc()
        sys.exit(1)
    RVC_ROOT = res[1]
    RVC_RUNTIME = fl.merge_dir_txt2(RVC_ROOT, 'Runtime',"python.exe")
    for i in injected["Injections"]:
        file_path = str(MadPath([i["target"]],
                            i["root"],
                            globals()))
        dest_path = str(MadPath([i["injection"]],
                            i["destination"],
                            globals()))
        logger.info(f"Injecting {file_path} to {dest_path}")
        shutil.copy2(file_path, dest_path)
    json_write = {"Build_Time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),"install_location": str(res[0]), "root_location": str(res[1])}
    with open(fl.merge_dir_txt(CONFIG_DIR, 'Build.json'), 'w') as f:
        json.dump(json_write, f)
    with open(fl.merge_dir_txt(BUILD__DIR, 'install.json'), 'w') as f:
        json.dump(json_write, f)

    CMD_BASE = [f"{RVC_RUNTIME}",
           "-m",
           "pip",
           "install",
           ]
    logger.info("Updating pip")
    subprocess.run([*CMD_BASE, "--upgrade", "pip"], check=True)
    logger.info("Installing pip requirements")
    for f in os.listdir(RVC_PIP_PACKAGE_INJECTION):
        if f.endswith(".txt"):
            req_file = fl.merge_dir_txt2(RVC_PIP_PACKAGE_INJECTION, f)
            logger.info(f"Installing pip requirements from {req_file}")
            cmd = [*CMD_BASE,
                   "-r",
                   str(req_file)]
            subprocess.run(cmd, check=True)
    logger.info("fixing setuptools issue")
    subprocess.run([*CMD_BASE, 
                    "setuptools<82.0.0",
                    "--force-reinstall"], check=True) # RVC can't work with setuptools>=82.0.0
