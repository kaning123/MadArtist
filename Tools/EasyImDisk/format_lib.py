import subprocess
import time
import file_lib as fl
import log_lib
class FormatDiskError(Exception):
    pass
def main(letter: str,max_retry = 3000,_await=10):
    logger = log_lib.LogStream("format_disk", dir_path=fl.merge_dir_txt(fl.get_my_dir(),'Log'), f_display=True, c_display=True).logger
    logger.info(f"开始格式化磁盘 {letter}，请勿关闭此窗口")
    bat_path = fl.merge_dir_txt2(fl.get_my_dir(), "format_disk.bat")
    subprocess.run([str(bat_path), letter], check=True)
    time.sleep(10)
    retry = 0
    while retry < max_retry:
        try:
            with open(fl.merge_dir_txt2(letter, "format_disk_log.txt"), "w") as f:
                f.write(f"检查格式化状态，尝试第 {retry+1} 次\n")
            return True
        except:
            retry += 1
            time.sleep(_await)
            continue
    logger.error(f"格式化失败，超时退出，已等待{max_retry*_await}秒")
    raise FormatDiskError(f"格式化失败，超时退出，已等待{max_retry*_await}秒")
if __name__ == "__main__":
    main("Z:")