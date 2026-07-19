import importlib

import os
import shutil
from pathlib import Path

def get_my_dir():
    return os.path.dirname(os.path.abspath(__file__))

def get_parent_dir(dir_path,depth=1):
    parent_path = Path(dir_path)
    for _ in range(depth):
        parent_path = parent_path.parent
    return parent_path

#print(get_parent_dir(get_my_dir(),6))

def merge_dir_txt(a,b):
    c=os.path.join(a,b)
    return c
def merge_dir_txt2(*TXT):
    return Path(os.path.join(*TXT))
def create_dir(path: Path, overwrite=False) -> bool:
    if overwrite and path.exists():
        shutil.rmtree(path)
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path.exists()
def get_dir_children_dirs(path: Path):
    return [item for item in path.iterdir() if item.is_dir()]
def get_dir_children_files(path: Path):
    return [item for item in path.iterdir() if item.is_file()]
def delete_dir(path: Path):
    return shutil.rmtree(path)
def delete_file(path: Path):
    return os.remove(path)
def file_exists(path: Path):
    path = Path(path)
    return path.exists()

def load_pkg_file(file = str(merge_dir_txt2(get_my_dir(), ".pkg_active"))):
    with open(file, "r") as f:
        l = f.readline()
        while l:
            yield l
            l = f.readline()

for i in load_pkg_file():
    globals()[i] = importlib.import_module(f'.{i}', package=__name__)

def load_generator(generator_name):
    module_name = globals()[generator_name]
    return module_name