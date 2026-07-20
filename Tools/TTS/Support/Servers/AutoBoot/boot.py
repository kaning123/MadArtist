from MadLib import MadProcessManager,MadCMD,MadPath
import json
import threading
import LogLib
import logging
import click
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console
import subprocess
from typing import List, Dict, Optional, Any
import file_lib as fl
import sys
from pathlib import Path
import time

console = Console()
logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click]),]
)
console.print("[bold green]MadArtist Servers AutoBoot Script[/bold green] - Version [red]Alpha_0.0.1_202607[/red]")
logger = LogLib.get_logger("AutoBoot").logger

MY_DIR = fl.get_my_dir()
CONFIG_DIR = fl.merge_dir_txt2(MY_DIR, "Config")
ROOT_DIR = str(Path(MY_DIR).parent)
PYTHON_EXECUTABLE = sys.executable
with open(str(fl.merge_dir_txt2(CONFIG_DIR, "Classes")), 'r') as f:
    CLASSES = f.readlines()

with open(str(fl.merge_dir_txt2(CONFIG_DIR, "ServerChoose.json")), 'r') as f:
    SERVER_CHOOSE = json.load(f)

def match_marks(servers_data, marks_data):
    # 1. 构建 Name -> Mark 的映射
    mark_map = {item["Name"]: item for item in marks_data["Marks"]}

    # 2. 遍历 Servers，匹配 Mark
    matched_results = []
    for server in servers_data["Servers"]:
        server_name = server["Name"]
        mark_info = mark_map.get(server_name)  # 若匹配不到则返回 None
        matched_results.append({
            "Server": server,
            "Mark": mark_info
        })

    # 3. 打印匹配结果（示例）
    for result in matched_results:
        logger.info(f"Server: {result['Server']['Name']}")
        if result["Mark"]:
            logger.info(f"  -> Mark Path: {result['Mark']['Path']}")
        else:
            logger.info(f"  -> No matching Mark found")
    return matched_results

def main():
    logger.info("Starting AutoBoot Script...")
    executions = []

    for CLASS in CLASSES:
        CLASS = CLASS.strip()
        if CLASS:
            logger.info(f"Searching for class: {CLASS}")
            subprocess.run([sys.executable,  
                            str(fl.merge_dir_txt2(ROOT_DIR, 
                                                CLASS, 
                                                "search_class.py")),
                            ])
            logger.info(f"Class {CLASS} search completed.")
            logger.info(f"Getting Mark for class: {CLASS}")
            with open(str(fl.merge_dir_txt2(ROOT_DIR, 
                                            CLASS, 
                                            "Config",
                                            "Marks.json",)),
                      'r') as f:
                marks = json.load(f)
                logger.info(f"Mark for class {CLASS} retrieved.")
            logger.info(f"Matching Marks for class: {CLASS}")
            matches = match_marks(SERVER_CHOOSE, marks)
            logger.debug(f"Matches: {matches}")
            logger.info(f"Getting Boot Script for class: {CLASS}")
            boots = []
            for match in matches:
                boots.append(match["Mark"]["Path"])
            logger.info(f"Boot Script for class {CLASS} retrieved.")
            logger.info(f"Running Boot Script for class: {CLASS}")
            for boot in boots:
                with open(boot, 'r', encoding='utf-8') as f:
                    boot = json.load(f)
                    logger.debug(f"Boot Script: {boot}")
                NewNameSpace = {}
                for k,v in boot["MadPathNameSpace"].items():
                    NewNameSpace[k] = str(MadPath(v, [], globals()))
                logger.debug(f"NewNameSpace: {NewNameSpace}")
                cmd = MadCMD(boot["Execution"], {**globals(), **NewNameSpace}).l
                executions.append(cmd)

    with MadProcessManager() as manager:
        for cmd in executions:
            manager.start_process(cmd)
            logger.info(f"Started process: {cmd}")

        while True:
            time.sleep(0.1)

if __name__ == "__main__":
    main()

            

        


            