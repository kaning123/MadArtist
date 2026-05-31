import sys
import os
import file_lib as fl
import subprocess
from pathlib import Path
import json
ROOT_DIR = str(Path(fl.get_my_dir()).parent)
BUILD__DIR = fl.merge_dir_txt(ROOT_DIR, 'Build_')
CONFIG_DIR = fl.merge_dir_txt(ROOT_DIR, 'Config')
INJECTION_DIR = fl.merge_dir_txt(ROOT_DIR, 'Injection')
with open(fl.merge_dir_txt(CONFIG_DIR, 'Build.json'), 'r') as f:
    json_data = json.load(f)
RVC_ROOT = json_data.get("root_location", "")
if RVC_ROOT == "":
    raise ModuleNotFoundError("RVC installation not found. Please run \"python build.py\" first.")
RVC_RUNTIME = fl.merge_dir_txt2(RVC_ROOT, 'Runtime',"python.exe")
os.chdir(str(RVC_ROOT))
cmd = ["cmd", "/c", f'{str(RVC_RUNTIME)}', 
       f'{str(fl.merge_dir_txt(RVC_ROOT, "infer-web-B.py"))}',
       "--pycmd",
       f"{str(RVC_RUNTIME)}",
       "--port",
       "7897",
       "--noautoopen",]
subprocess.run(cmd)

