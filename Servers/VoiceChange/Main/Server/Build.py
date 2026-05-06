print("MadArtist Server Build - Version Alpha_0.0.1_202606")
import os
from pathlib import Path
import file_lib as fl
import json
import time
import traceback
ROOT_DIR = str(Path(fl.get_my_dir()).parent)
BUILD__DIR = fl.merge_dir_txt(ROOT_DIR, 'Build_')
CONFIG_DIR = fl.merge_dir_txt(ROOT_DIR, 'Config')
import sys
#print(sys.path)
sys.path.append(ROOT_DIR)
try:
    import Build_.build as build
except:
    traceback.print_exc()
finally:
    del sys.path[-1]

if __name__ == '__main__':
    res = build.main()
    json_write = {"Build_Time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),"install_location": str(res[0]), "root_location": str(res[1])}
    with open(fl.merge_dir_txt(CONFIG_DIR, 'Build.json'), 'w') as f:
        json.dump(json_write, f)
    with open(fl.merge_dir_txt(BUILD__DIR, 'install.json'), 'w') as f:
        json.dump(json_write, f)
