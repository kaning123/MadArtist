print("MadArtist Server Build - Version Alpha_0.0.1_202606")
import os
from pathlib import Path
import file_lib as fl
ROOT_DIR = str(Path(fl.get_my_dir()).parent)
import sys
#print(sys.path)
sys.path.append(ROOT_DIR)
import Build_.build as build
del sys.path[-1]

if __name__ == '__main__':
    build.main()