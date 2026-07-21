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
    datefmt="[%Y.%m.%d-%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click]),]
)
logger = logging.getLogger(__name__)

#logger.info("Hello, World!")

#logger.exception("This is an exception.")
logger.error("This is an error.")
logger.warning("This is a warning.")
logger.info("This is an info message.")
logger.debug("This is a debug message.")
time.sleep(5)
logger.critical("This is a critical message.")