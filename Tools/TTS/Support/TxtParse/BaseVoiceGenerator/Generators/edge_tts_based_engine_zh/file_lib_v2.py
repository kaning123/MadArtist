import shutil
import threading
import atexit
from pathlib import Path
from typing import Optional, List, Union, IO
from rich.console import Console
from rich.logging import RichHandler
import logging

# ---------- 日志配置 ----------
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console)]
)
logger = logging.getLogger("temp_manager")

# ---------- 全局临时路径管理与清理 ----------
_global_temp_paths: set = set()
_global_lock = threading.Lock()

def _register_temp_path(path: Path):
    with _global_lock:
        _global_temp_paths.add(path)

def _unregister_temp_path(path: Path):
    with _global_lock:
        _global_temp_paths.discard(path)

def _cleanup_all_temp():
    with _global_lock:
        paths = list(_global_temp_paths)
        _global_temp_paths.clear()
    for p in paths:
        try:
            if p.is_file():
                p.unlink()
                logger.info(f"Deleted temp file: {p}")
            elif p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
                logger.info(f"Deleted temp dir: {p}")
        except Exception as e:
            logger.error(f"Failed to delete {p}: {e}")

atexit.register(_cleanup_all_temp)

# ---------- 基础工具函数 ----------
def get_my_dir() -> Path:
    return Path(__file__).resolve().parent

def get_parent_dir(path: Union[Path, str], depth: int = 1) -> Path:
    p = Path(path)
    for _ in range(depth):
        p = p.parent
    return p

def merge_dir_txt(a: Union[Path, str], b: str) -> Path:
    return Path(a) / b

def merge_dir_txt2(*parts: Union[Path, str]) -> Path:
    return Path(*parts)

def create_dir(path: Union[Path, str], overwrite: bool = False) -> bool:
    p = Path(path)
    if overwrite and p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)
    return p.exists()

def get_dir_children_dirs(path: Union[Path, str]) -> List[Path]:
    p = Path(path)
    return [item for item in p.iterdir() if item.is_dir()]

def get_dir_children_files(path: Union[Path, str]) -> List[Path]:
    p = Path(path)
    return [item for item in p.iterdir() if item.is_file()]

def delete_dir(path: Union[Path, str]) -> None:
    p = Path(path)
    if p.exists():
        shutil.rmtree(p)
        logger.info(f"Deleted directory: {p}")

def delete_file(path: Union[Path, str]) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()
        logger.info(f"Deleted file: {p}")

def file_exists(path: Union[Path, str]) -> bool:
    return Path(path).exists()

# ---------- 默认临时路径 ----------
DEFAULT_TEMP_PATH = get_my_dir() / "Temp"
DEFAULT_TEMP_PATH.mkdir(parents=True, exist_ok=True)

def _convent_tmp_path(filename: str, temp_path: Path = DEFAULT_TEMP_PATH) -> Path:
    return temp_path / filename

# ---------- TempFile 类（线程安全，支持文件对象保存） ----------
class TempFile:
    def __init__(
        self,
        filename: str,
        temp_path: Path = DEFAULT_TEMP_PATH,
        auto_delete: bool = True
    ):
        self.path = _convent_tmp_path(filename, temp_path)
        self.auto_delete = auto_delete
        self._lock = threading.Lock()
        self._file_obj: Optional[IO] = None   # 保存的文件对象

        if auto_delete:
            _register_temp_path(self.path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        if self.auto_delete:
            self.remove()

    def __del__(self):
        # 尽量保证资源释放
        self.close()

    # ---------- 文件对象管理 ----------
    def open(self, mode: str = 'r') -> IO:
        """打开文件，返回文件对象，并内部保存引用。若已有打开的文件对象，则先关闭再打开新的。"""
        with self._lock:
            self._close_internal()   # 关闭旧的对象
            try:
                self._file_obj = self.path.open(mode)
                logger.debug(f"Opened file {self.path} in mode '{mode}'")
                return self._file_obj
            except Exception as e:
                logger.error(f"Failed to open {self.path} with mode '{mode}': {e}")
                raise

    def close(self):
        """关闭当前持有的文件对象（若有）"""
        with self._lock:
            self._close_internal()

    def _close_internal(self):
        """内部方法：关闭文件对象并置 None（调用者需持有锁）"""
        if self._file_obj is not None:
            try:
                self._file_obj.close()
            except Exception as e:
                logger.warning(f"Error closing file object for {self.path}: {e}")
            finally:
                self._file_obj = None

    # ---------- 文件操作（自动关闭文件对象） ----------
    def exists(self) -> bool:
        with self._lock:
            return self.path.exists()

    def read(self) -> Optional[str]:
        with self._lock:
            self._close_internal()   # 关闭文件对象以确保能正常读取
            try:
                return self.path.read_text(encoding='utf-8')
            except FileNotFoundError:
                logger.warning(f"File not found: {self.path}")
                return None
            except PermissionError as e:
                logger.error(f"Permission denied reading {self.path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error reading {self.path}: {e}")
                raise

    def write(self, content: str, overwrite: bool = True):
        with self._lock:
            self._close_internal()   # 关闭文件对象
            try:
                if overwrite or not self.path.exists():
                    self.path.write_text(content, encoding='utf-8')
                    logger.info(f"Written to {self.path}")
                else:
                    logger.warning(f"File exists and overwrite=False: {self.path}")
            except PermissionError as e:
                logger.error(f"Permission denied writing {self.path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error writing {self.path}: {e}")
                raise

    def create(self, overwrite: bool = False):
        with self._lock:
            self._close_internal()   # 关闭文件对象
            try:
                if overwrite or not self.path.exists():
                    self.path.touch()
                    logger.info(f"Created file: {self.path}")
                else:
                    logger.info(f"File already exists: {self.path}")
            except PermissionError as e:
                logger.error(f"Permission denied creating {self.path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error creating {self.path}: {e}")
                raise

    def remove(self):
        with self._lock:
            self._close_internal()   # 先关闭文件对象，确保可删除
            try:
                if self.path.exists():
                    self.path.unlink()
                    logger.info(f"Removed file: {self.path}")
                    if self.auto_delete:
                        _unregister_temp_path(self.path)
            except PermissionError as e:
                logger.error(f"Permission denied removing {self.path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error removing {self.path}: {e}")
                raise

    # ---------- 特殊方法 ----------
    def __str__(self) -> str:
        return str(self.path)

    def __repr__(self) -> str:
        return f"TempFile('{self.path.name}', temp_path='{self.path.parent}')"

    def __eq__(self, other):
        if isinstance(other, TempFile):
            return self.path == other.path
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        if isinstance(other, TempFile):
            return [str(self.path), str(other.path)]
        raise TypeError("Can only add TempFile to TempFile")

# ---------- TempDir 类（保持不变） ----------
class TempDir:
    def __init__(
        self,
        dirname: str,
        temp_path: Path = DEFAULT_TEMP_PATH,
        auto_delete: bool = True
    ):
        self.path = temp_path / dirname
        self.auto_delete = auto_delete
        self._lock = threading.Lock()

        if auto_delete:
            _register_temp_path(self.path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.auto_delete:
            self.remove()

    def exists(self) -> bool:
        with self._lock:
            return self.path.exists() and self.path.is_dir()

    def create(self, overwrite: bool = False):
        with self._lock:
            try:
                if self.path.exists() and not self.path.is_dir():
                    raise ValueError(f"Path {self.path} exists but is not a directory")
                if overwrite and self.path.exists():
                    shutil.rmtree(self.path)
                    logger.info(f"Removed existing directory: {self.path}")
                self.path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {self.path}")
            except PermissionError as e:
                logger.error(f"Permission denied creating {self.path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error creating {self.path}: {e}")
                raise

    def remove(self):
        with self._lock:
            try:
                if self.path.exists():
                    shutil.rmtree(self.path)
                    logger.info(f"Removed directory: {self.path}")
                    if self.auto_delete:
                        _unregister_temp_path(self.path)
            except PermissionError as e:
                logger.error(f"Permission denied removing {self.path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error removing {self.path}: {e}")
                raise

    def __str__(self) -> str:
        return str(self.path)

    def __repr__(self) -> str:
        return f"TempDir('{self.path.name}', temp_path='{self.path.parent}')"

# ---------- FastAPI 辅助函数（不变） ----------
def process_fastapi_uploadfile_list(files: list):
    files_ = []
    for file in files:
        files_.append(("files", (file.filename, file.file, file.content_type)))
    return files_

# ---------- 示例用法 ----------
if __name__ == "__main__":
    # 测试文件对象保存
    with TempFile("example.txt", auto_delete=True) as tf:
        # 打开文件并获得文件对象
        f = tf.open('w')
        f.write("Hello, world!\n")
        f.write("This is a test.")
        f.close()   # 可以手动关闭，但 TempFile 也会在退出时关闭

        # 重新打开读取
        with tf.open('r') as rf:
            content = rf.read()
            print(content)

        # 也可以直接使用 read/write 方法（它们会自动关闭文件对象）
        tf.write("New content", overwrite=True)
        print(tf.read())
    # 退出 with 块后自动删除文件