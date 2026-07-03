from .easy_imdisk import *

import ctypes
import string

def get_free_drives(exclude_ab=True):
    """
    获取当前系统中未被占用的盘符列表。
    
    参数:
        exclude_ab (bool): 是否排除 A: 和 B:（传统软驱保留位），默认为 True。
    
    返回:
        list: 空闲盘符字符串列表，例如 ['D:', 'E:', ...]
    """
    # 获取所有逻辑驱动器的位掩码（32位整数，低26位有效，对应 A-Z）
    drives_bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    
    free_drives = []
    # 盘符字母列表，默认全量 A-Z
    letters = string.ascii_uppercase
    for i, letter in enumerate(letters):
        # 检查第 i 位是否为 0（未占用）
        if not (drives_bitmask & (1 << i)):
            drive = f"{letter}:"
            # 可选项：排除 A: 和 B:
            if exclude_ab and drive in ('A:', 'B:'):
                continue
            free_drives.append(drive)
    return free_drives
