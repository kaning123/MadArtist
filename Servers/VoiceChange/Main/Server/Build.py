print("MadArtist Server Build - Version Alpha_0.0.1_202606")
import os
from pathlib import Path
import file_lib as fl
import json
import time
import shutil
import traceback
ROOT_DIR = str(Path(fl.get_my_dir()).parent)
BUILD__DIR = fl.merge_dir_txt(ROOT_DIR, 'Build_')
CONFIG_DIR = fl.merge_dir_txt(ROOT_DIR, 'Config')
INJECTION_DIR = fl.merge_dir_txt2(ROOT_DIR, 'Server', 'Injection')
INJECTION2_DIR = fl.merge_dir_txt2(ROOT_DIR, 'Server', 'Injection2')
import sys
#print(sys.path)
sys.path.append(ROOT_DIR)
try:
    import Build_.build as build
    import Build_.log_lib as log_lib
except:
    traceback.print_exc()
finally:
    del sys.path[-1]
from pathlib import Path
logger = log_lib.get_logger("Build", fl.merge_dir_txt(BUILD__DIR, "Log"), log_lib.DEBUG, f_display=True).logger
class MadPath:
    def parse_list(self,l):
        for i in range(len(l)):
            if l[i].startswith("~~##") and l[i].endswith("##~~"):
                l[i] = self.env[l[i].replace("~~##", "").replace("##~~", "")]
        return l
    def __init__(self, l:list, root:list,env:dict):
        self.env = env
        self.root = self.parse_list(root)
        self.l = self.parse_list(l)
        self.path = fl.merge_dir_txt2(*self.root,*self.l)
    def __str__(self) -> str:
        return str(self.path)
                

if __name__ == '__main__':
    res = build.main()
    for i in INJECTION_DIR.iterdir():
        if i.is_file():
            shutil.copy2(str(i), str(res[1]))
        elif i.is_dir():
            shutil.copytree(str(i), str(fl.merge_dir_txt2(res[1], i.name)), dirs_exist_ok=True)
    try:
        with open(fl.merge_dir_txt(INJECTION2_DIR, "inject.json"), "r") as f:
            injected = json.load(f)
    except:
        traceback.print_exc()
        sys.exit(1)
    RVC_ROOT = res[1]
    for i in injected["Injections"]:
        file_path = str(MadPath(list(i["target"]),
                            i["root"],
                            globals()))
        dest_path = str(MadPath(list(i["injection"]),
                            i["destination"],
                            globals()))
        logger.info(f"Injecting {file_path} to {dest_path}")
        shutil.copy2(file_path, dest_path)
    json_write = {"Build_Time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),"install_location": str(res[0]), "root_location": str(res[1])}
    with open(fl.merge_dir_txt(CONFIG_DIR, 'Build.json'), 'w') as f:
        json.dump(json_write, f)
    with open(fl.merge_dir_txt(BUILD__DIR, 'install.json'), 'w') as f:
        json.dump(json_write, f)
