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

def process_fastapi_uploadfile_list(files: list):
    files_ = []
    for file in files:
        files_.append(("files", (file.filename, file.file, file.content_type)))
    return files_

DEFAULT_TEMP_PATH = merge_dir_txt2(get_my_dir(),"Temp")
if not os.path.exists(DEFAULT_TEMP_PATH):
    os.makedirs(DEFAULT_TEMP_PATH)
DEFAULT_TEMP_PATH = str(DEFAULT_TEMP_PATH)

def _convent_tmp_path(filename,temp_path=DEFAULT_TEMP_PATH):
    return str(merge_dir_txt2(temp_path,filename))

class TempFile(object):
    def __init__(self, filename, temp_path=DEFAULT_TEMP_PATH):
        self.fname = filename
        self.temp_path = temp_path
        self.ful_pth = _convent_tmp_path(filename,temp_path=temp_path)
        self.fobj = None
    def __str__(self):
        return self.ful_pth
    def __del__(self):
        self.clear_fobj()
    def __repr__(self):
        selfargs = {'fname': self.fname,"temp_path": self.temp_path, "ful_pth": self.ful_pth, "fobj": self.fobj}
        return f"TempFile('{self.fname}')\nselfargs:{selfargs}"
    def __eq__(self, value):
        try:
            return self.ful_pth == value.ful_pth
        except AttributeError:
            return False
    def __ne__(self, value):
        try:
            return self.ful_pth != value.ful_pth
        except AttributeError:
            return True
    def __add__(self, value):
        return [self.ful_pth, value.ful_pth]
    def find(self):
        try:
            with open(self.ful_pth, 'r') as f:
                return f.read(), True
        except FileNotFoundError:
            return None, False
    def create(self,overwrite=False):
        fres = self.find()
        if overwrite:
            f = open(self.ful_pth, 'w')
            f.write('')
            self.clear_fobj()
            self.fobj = f
        else:
            if not fres[1]:
                f = open(self.ful_pth, 'w')
                f.write('')
                self.clear_fobj()
                self.fobj = f
    def open(self,mode='r'):
        f = open(self.ful_pth, mode)
        self.fobj = f
    def clear_fobj(self):
        if self.fobj is not None:
            self.fobj.close()
            self.fobj = None
    def remove(self):
        try:
            os.remove(self.ful_pth)
        except FileNotFoundError:
            pass
    

class TempDir(object):
    def __init__(self, dirname):
        self.dname = dirname
        self.ful_pth = _convent_tmp_path(dirname)
    def find(self):
        try:
            os.listdir(self.ful_pth)
            return True
        except FileNotFoundError:
            return False
    def create(self, overwrite=False):
        fres = self.find()
        if os.path.isfile(self.ful_pth):
            raise ValueError(f"Path {self.ful_pth} is a file, not a directory")
        if fres:
            if overwrite:
                shutil.rmtree(self.ful_pth)
                os.makedirs(self.ful_pth)

        if overwrite:
            os.makedirs(self.ful_pth, exist_ok=True)
        else:
            if not fres:
                os.makedirs(self.ful_pth)
    def remove(self):
        try:
            shutil.rmtree(self.ful_pth)
        except FileNotFoundError:
            pass

