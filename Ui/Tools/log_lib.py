import logging
import logging.handlers

import file_lib
import time_lib
DEFAULT_THEME = logging.Formatter(f'[%(asctime)s][%(name)s/%(levelname)s][Func:%(funcName)s][%(filename)s:%(lineno)d] : %(message)s',datefmt='%Y-%m-%d/%H:%M:%S')
LONG_THEME = logging.Formatter(f'[%(asctime)s:%(msecs)d][%(processName)s:%(process)d][%(threadName)s:%(thread)d][%(name)s/%(levelname)s][Func:%(funcName)s][%(module)s:%(lineno)d] - at %(pathname)s: %(message)s',datefmt='%Y-%m-%d/%H:%M:%S')
INFO = logging.INFO
DEBUG = logging.DEBUG
WARN = logging.WARN
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

POOL:set = set() #LOGGER POOL
def get_unique_name(name):
    _id = 1
    if name not in POOL:
        return name
    while name in POOL:
        _id += 1
        name = f'{name}_{_id}'
    return name
class LogStream:
    def __init__(self, logger_name,dir_path,LVL=DEBUG,file_name=f'log.log',theme = DEFAULT_THEME,c_display=True,f_display=False):
        
        file_name = f'logger_[{logger_name}][{time_lib.get_time_full()}]_{file_name}'
        filepath = file_lib.merge_dir_txt(dir_path,file_name)

        logger_name = get_unique_name(logger_name)
        POOL.add(logger_name)

        self.name = logger_name
        self.dir_path = dir_path
        self.file_name = file_name
        self.filepath = filepath
        self.theme = theme
        self.c_display = c_display
        self.f_display = f_display

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(LVL)

        if c_display:
            self.console = logging.StreamHandler()
            self.console.setLevel(LVL)
            self.console.setFormatter(theme)
            self.logger.addHandler(self.console)
        if f_display:
            self.file = logging.handlers.RotatingFileHandler(filepath, mode='w', maxBytes=1024*1024*10, backupCount=5)
            self.file.setLevel(LVL)
            self.file.setFormatter(theme)
            self.logger.addHandler(self.file)

        self.lvl = LVL
    def log(self,*MSG,LVL=None,joiner=' '):
        if LVL is None:
            LVL = self.lvl
        MSG = joiner.join([str(i) for i in MSG])
        if LVL == INFO:
            self.logger.info(MSG)
        elif LVL == DEBUG:
            self.logger.debug(MSG)
        elif LVL == WARN:
            self.logger.warning(MSG)
        elif LVL == ERROR:
            self.logger.error(MSG)
        elif LVL == CRITICAL:
            self.logger.critical(MSG)
        else:
            self.logger.debug(MSG)
    def info(self,*MSG,joiner=' '):
        self.log(*MSG,LVL=INFO,joiner=joiner)
    def debug(self,*MSG,joiner=' '):
        self.log(*MSG,LVL=DEBUG,joiner=joiner)
    def warn(self,*MSG,joiner=' '):
        self.log(*MSG,LVL=WARN,joiner=joiner)
    def error(self,*MSG,joiner=' '):
        self.log(*MSG,LVL=ERROR,joiner=joiner)
    def critical(self,*MSG,joiner=' '):
        self.log(*MSG,LVL=CRITICAL,joiner=joiner)
        


if __name__ == '__main__':
    log = LogStream('test',r'D:\Desktop\MidBox\ToolChain\bootable\Layer\GOD_BLOCK\log',LVL=DEBUG)
    log.log('test info',LVL=INFO)
    log.log('test debug',LVL=DEBUG)
    log.log('test warn',LVL=WARN)
    log2 = LogStream('test',r'D:\Desktop\MidBox\ToolChain\bootable\Layer\GOD_BLOCK\log',LVL=DEBUG,theme=LONG_THEME,f_display=True)
    log2.log('test2 info',LVL=INFO)