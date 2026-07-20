import os
import sys
import logging
import click
from rich.logging import RichHandler
from rich.console import Console
import file_lib as fl
import json
console = Console()
logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click]),]
)
logger = logging.getLogger("MadArtist_Class_Search")
class MadPath:
    def parse_list(self,l:list[str]):
        for i in range(len(l)):
            if l[i].startswith("~~##") and l[i].endswith("##~~"):
                l[i] = self.env[l[i].replace("~~##", "").replace("##~~", "")]
        return l
    def __init__(self, l:list, root:list,env:dict):
        logger.info(f"MadPath initialized with l: {l} and root: {root}")
        logger.info(f"MadPath initialized with env: {env}")
        self.env = env
        self.root = self.parse_list(root)
        self.l = self.parse_list(l)
        self.path = fl.merge_dir_txt2(*self.root,*self.l)
    def __str__(self) -> str:
        return str(self.path)

class MadCMD:
    def parse_list(self,l:list[str]):
        for i in range(len(l)):
            if l[i].startswith("-<") and l[i].endswith(">-"):
                l[i] = self.env[l[i].replace("-<", "").replace(">-", "")]
        return l
    def __init__(self, l:list, root:list,env:dict):
        logger.info(f"MadCMD initialized with l: {l} and root: {root}")
        logger.info(f"MadCMD initialized with env: {env}")
        self.env = env
        self.l = self.parse_list(l)

console.print("[bold green]MadArtist Class Search Script[/bold green] - Version [red]Alpha_0.0.1_202607[/red]")

Marks = {"Marks":[]}

MY_DIR = fl.get_my_dir()
CONFIG_DIR = fl.merge_dir_txt2(MY_DIR, "Config")

with open(fl.merge_dir_txt2(CONFIG_DIR, "Class.json"), 'r') as f:
    CLASS_NAME = json.load(f)['Name']

for d in os.listdir(MY_DIR):
    if os.path.isdir(os.path.join(MY_DIR, d)):
        logger.info(f"Found directory: {d}")
        Mark_JSON_Path = fl.merge_dir_txt2(MY_DIR, d, "Config", "Mark.json")
        if os.path.exists(Mark_JSON_Path):
            logger.info(f"Mark.json found in {Mark_JSON_Path}")
            with open(Mark_JSON_Path, 'r') as f:
                Mark_JSON = json.load(f)
                if Mark_JSON.get("class","") == CLASS_NAME:
                    logger.info(f"Class match found in {Mark_JSON_Path}")
                    Name = Mark_JSON.get("Name","")
                    Marks["Marks"].append({"Name": Name, "Path": str(Mark_JSON_Path)})

with open(fl.merge_dir_txt2(CONFIG_DIR, "Marks.json"), 'w') as f:
    json.dump(Marks, f, indent=4)