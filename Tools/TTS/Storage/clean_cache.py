import os
import shutil
from pathlib import Path

print("MadArtist Manual Cache Cleaner Script - Version Alpha_0.0.1_202607")
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

def load_pkg_file(file = str(merge_dir_txt2(get_my_dir(), ".protect_file"))):
    with open(file, "r") as f:
        l = f.readlines()
        return l

l = load_pkg_file()
l = [item.strip() for item in l]
dlist = []
for f in os.listdir(get_my_dir()):
    if f not in l:
        print(f)
        dlist.append(f)

print("Do you want to delete these files below?")
for f in dlist:
    print(f)

res = input("(y/n)> ")
if res.lower() == "y":
    for f in dlist:
        if os.path.isfile(Path(get_my_dir(), f)):
            delete_file(Path(get_my_dir(), f))
        elif os.path.isdir(Path(get_my_dir(), f)):
            shutil.rmtree(Path(get_my_dir(), f))
    print("Files deleted successfully.")
else:
    print("Files will not be deleted.")

