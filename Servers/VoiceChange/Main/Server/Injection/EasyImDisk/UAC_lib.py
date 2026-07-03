import ctypes
import subprocess
import shlex

def run_as_admin(cmdline: str, cwd=None, wait=True):
    """
    以管理员权限运行一条命令（支持任意 exe 或批处理）
    :param cmdline: 完整命令行字符串，例如 r"C:\a.exe /S /D=C:\123"
    :param cwd:     工作目录，None 表示不指定
    :param wait:    是否阻塞等待子进程结束
    :return:        子进程 returncode（若 wait=True），否则立即返回 None
    """
    SEE_MASK_NOCLOSEPROCESS = 0x00000040
    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_uint32),
            ("fMask", ctypes.c_uint32),
            ("hwnd", ctypes.c_void_p),
            ("lpVerb", ctypes.c_wchar_p),
            ("lpFile", ctypes.c_wchar_p),
            ("lpParameters", ctypes.c_wchar_p),
            ("lpDirectory", ctypes.c_wchar_p),
            ("nShow", ctypes.c_int32),
            ("hInstApp", ctypes.c_void_p),
            ("lpIDList", ctypes.c_void_p),
            ("lpClass", ctypes.c_wchar_p),
            ("hkeyClass", ctypes.c_void_p),
            ("dwHotKey", ctypes.c_uint32),
            ("hMonitor", ctypes.c_void_p),
            ("hProcess", ctypes.c_void_p),
        ]

    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
    sei.fMask = SEE_MASK_NOCLOSEPROCESS
    sei.lpVerb = "runas"               # 关键：触发 UAC
    sei.lpFile = shlex.split(cmdline)[0]
    sei.lpParameters = subprocess.list2cmdline(shlex.split(cmdline)[1:])
    sei.lpDirectory = cwd
    sei.nShow = 1                      # SW_SHOWNORMAL

    if ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei)):
        if wait:
            ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, -1)
            rc = ctypes.c_uint32()
            ctypes.windll.kernel32.GetExitCodeProcess(sei.hProcess, ctypes.byref(rc))
            ctypes.windll.kernel32.CloseHandle(sei.hProcess)
            return rc.value
        return None
    else:
        raise RuntimeError("ShellExecuteEx(runas) 失败，用户可能拒绝了 UAC")
def subproc(*CMDTXT,cwd=None,wait=True,join= ' '):
    """以管理员权限运行一条命令（支持任意 exe 或批处理）"""
    cmdline = join.join(CMDTXT)
    return run_as_admin(cmdline, cwd=cwd, wait=wait)
