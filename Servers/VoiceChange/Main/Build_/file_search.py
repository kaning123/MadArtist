import os
from pathlib import Path
from . import file__lib as fl
from . import log_lib as log
import re
logger = log.LogStream("FileSearch",fl.merge_dir_txt2(fl.get_my_dir(),"Log"),file_name="file_search.log",c_display=True,f_display=False).logger
class File:
    def __init__(self, file_path,disable_exist_check=True):
        if not os.path.exists(file_path) and not disable_exist_check:
            raise FileNotFoundError(f"File {file_path} not found")
        if not os.path.isfile(file_path) and not disable_exist_check:
            raise ValueError(f"Path {file_path} is not a file")
        self.file_name = fl.split_path(file_path)[-1]
        self.store_location = fl.get_parent_dir(file_path)
        self.file_path = file_path

    def __str__(self):
        return self.file_name
class Directory:
    def __init__(self, dir_path):
        if not os.path.exists(dir_path):
            raise FileNotFoundError(f"Directory {dir_path} not found")
        if not os.path.isdir(dir_path):
            raise ValueError(f"Path {dir_path} is not a directory")
        self.dir_name = fl.split_path(dir_path)[-1]
        self.store_location = fl.get_parent_dir(dir_path)
        self.dir_path = dir_path

    def __str__(self):
        return self.dir_name
def get_all_file_data(path) -> list[File]:
    file_data = []
    if not os.path.exists(path):
        return file_data
    
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            file_data.append(File(file_path))
    return file_data
def get_all_dir_data(path) -> list[Directory]:
    dir_data = []
    if not os.path.exists(path):
        return dir_data
    logger.debug(f"Searching in {path}")
    for root, dirs, files in os.walk(path):
        for dir_ in dirs:
            dir_path = os.path.join(root, dir_)
            dir_data.append(Directory(dir_path))
    return dir_data
def search_file_by_name(path, name) -> list[File]:
    logger.debug(f"Searching for {name} in {path}")
    file_data = get_all_file_data(path)
    result = []
    for file in file_data:
        if re.search(name, file.file_name):
            result.append(file)
    return result
def search_dir_by_name(path, name) -> list[Directory]:
    logger.debug(f"Searching for {name} in {path}")
    dir_data = get_all_dir_data(path)
    result = []
    for dir_ in dir_data:
        if re.search(name, dir_.dir_name):
            result.append(dir_)
    return result
def strict_search_file_by_name(path, name) -> list[File]:
    logger.debug(f"Searching for {name} in {path}")
    file_data = get_all_file_data(path)
    result = []
    for file in file_data:
        if file.file_name == name:
            result.append(file)
    return result
def strict_search_dir_by_name(path, name) -> list[Directory]:
    logger.debug(f"Searching for {name} in {path}")
    dir_data = get_all_dir_data(path)
    result = []
    for dir_ in dir_data:
        if dir_.dir_name == name:
            result.append(dir_)
    return result
if __name__ == '__main__':
    file_data = search_file_by_name("E:/GPTSoVITS/","ffmpeg.exe")
    for file in file_data:
        print(str(file)+" "+str(file.store_location))