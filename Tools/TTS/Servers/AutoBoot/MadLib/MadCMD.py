from . import file_lib as fl
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console
import subprocess
import click
import logging
import sys
from pathlib import Path

console = Console()
logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click]),]
)
console.print("[bold green]MadArtist Servers AutoBoot Script[/bold green] - Version [red]Alpha_0.0.1_202607[/red]")
logger = logging.getLogger(__name__)

class MadCMD:
    def parse_list(self,l:list[str]):
        for i in range(len(l)):
            if l[i].startswith("-<") and l[i].endswith(">-"):
                l[i] = self.env[l[i].replace("-<", "").replace(">-", "")]
        return l
    def __init__(self, l:list, env:dict):
        #logger.info(f"MadCMD initialized with l: {l} and root: {root}")
        logger.info(f"MadCMD initialized with env: {env}")
        self.env = env
        self.l = self.parse_list(l)
    