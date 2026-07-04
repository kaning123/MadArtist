import threading
import LogLib
import logging
import click
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console

console = Console()
logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%Y.%m.%d-%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click]),]
)

logger = logging.getLogger(__name__)

