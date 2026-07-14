import threading
import logging
import click
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console
import subprocess
from typing import List, Dict, Optional, Any

console = Console()
logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_suppress=[click]),]
)

logger = logging.getLogger(__name__)


POOL_:set = set() #LOGGER POOL
def get_unique_name(name):
    _id = 1
    if name not in POOL_:
        POOL_.add(name)
        return name
    while name in POOL_:
        _id += 1
        name = f'{name}_{_id}'
    POOL_.add(name)
    return name
class MadProcessManager:
    """多线程外部进程管理器。

    每个进程在一个独立线程中运行，线程负责读取 stdout/stderr 并记录日志。
    支持启动、停止、列出进程和批量停止。
    """

    def __init__(self, name: str = "MadProcessManager"):
        self._processes: Dict[int, dict] = {}  # pid -> {'process': Popen, 'thread': Thread}
        self._lock = threading.Lock()
        self._name = get_unique_name(name)

    def start_process(self, cmd: List[str], **popen_kwargs) -> int:
        """启动外部进程，返回进程 PID。

        Args:
            cmd: 命令行参数列表，如 ["ping", "google.com"]
            **popen_kwargs: 传递给 subprocess.Popen 的额外参数（如 env, cwd 等）

        Returns:
            进程 PID (int)
        """
        # 强制以管道方式捕获输出
        popen_kwargs.setdefault('stdout', subprocess.PIPE)
        popen_kwargs.setdefault('stderr', subprocess.PIPE)
        popen_kwargs.setdefault('universal_newlines', True)   # 文本模式
        popen_kwargs.setdefault('bufsize', 1)                 # 行缓冲

        proc = subprocess.Popen(cmd, **popen_kwargs)
        pid = proc.pid

        # 启动监控线程
        thread = threading.Thread(
            target=self._run_process,
            args=(proc, pid),
            daemon=True,
            name=f"ProcessMonitor-{pid}"
        )

        with self._lock:
            self._processes[pid] = {'process': proc, 'thread': thread}

        thread.start()
        logger.info(f"Started process {pid} with command: {' '.join(cmd)}")
        return pid

    def _run_process(self, proc: subprocess.Popen, pid: int):
        """线程目标函数：读取 stdout/stderr 直到进程结束。"""
        def read_stream(stream, log_func, prefix: str):
            """逐行读取流并记录日志，流关闭时自动退出。"""
            try:
                for line in iter(stream.readline, ''):
                    if line:
                        log_func(f"{prefix} {line.rstrip()}")
            except Exception as e:
                logger.error(f"Error reading {prefix}: {e}")
            finally:
                stream.close()

        # 启动两个读取子线程（分别处理 stdout 和 stderr）
        t_out = threading.Thread(
            target=read_stream,
            args=(proc.stdout, logger.info, f"[PID {pid} STDOUT]"),
            daemon=True
        )
        t_err = threading.Thread(
            target=read_stream,
            args=(proc.stderr, logger.error, f"[PID {pid} STDERR]"),
            daemon=True
        )
        t_out.start()
        t_err.start()

        # 等待进程结束
        proc.wait()

        # 等待读取线程完成（流已关闭，线程很快退出）
        t_out.join(timeout=1)
        t_err.join(timeout=1)

        # 从管理列表中移除
        with self._lock:
            self._processes.pop(pid, None)

        logger.info(f"Process {pid} finished with return code {proc.returncode}")

    def stop_process(self, pid: int, timeout: float = 5.0) -> bool:
        """终止指定进程，并等待其结束。

        Args:
            pid: 进程 PID
            timeout: 等待进程正常退出的超时时间（秒），超时后强制 kill

        Returns:
            成功返回 True，进程不存在返回 False
        """
        with self._lock:
            info = self._processes.get(pid)
            if not info:
                logger.warning(f"Process {pid} not found")
                return False
            proc = info['process']

        # 先尝试温和终止
        proc.terminate()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # 强制杀死
            proc.kill()
            proc.wait()

        logger.info(f"Process {pid} stopped")
        return True

    def list_processes(self) -> List[int]:
        """返回当前管理的所有进程 PID 列表。"""
        with self._lock:
            return list(self._processes.keys())

    def stop_all(self, timeout: float = 5.0):
        """停止所有正在管理的进程。"""
        pids = self.list_processes()
        for pid in pids:
            self.stop_process(pid, timeout)

    def is_running(self, pid: int) -> bool:
        """检查指定进程是否仍在管理列表中（运行中）。"""
        with self._lock:
            return pid in self._processes
    
    def __exit__(self, exc_type, exc, tb):
        if exc_type == KeyboardInterrupt:
            console.print(f"[bold green]Exiting...[/bold green] - [bold cyan]{self._name}[/bold cyan]")
        self.stop_all()

    def __del__(self):
        self.stop_all()

    def __enter__(self):
        console.print(f"MadProcessManager [bold cyan]{self._name}[/bold cyan] started")
        return self