import file_lib as fl
import os
import json
import subprocess

CONFIG_DIR = fl.merge_dir_txt2(fl.get_my_dir(),"Config")
with open(str(fl.merge_dir_txt2(CONFIG_DIR,"Location.json")), "r") as f:
    config = json.load(f)
EVERYTHING_EXE_PATH = fl.merge_dir_txt2(fl.get_my_dir(),*config["Location_EveryThing_exe_path"])
if not os.path.exists(EVERYTHING_EXE_PATH):
    EVERYTHING_INSTALL_PATH = fl.merge_dir_txt2(fl.get_my_dir(),*config["Install_EveryThing_path"])
    subprocess.Popen([EVERYTHING_INSTALL_PATH])
print(f"{EVERYTHING_EXE_PATH} -start-service")
subprocess.Popen([EVERYTHING_EXE_PATH,"-start-service"])