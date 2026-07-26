print("MadArtist UV Add Script - Version Alpha_0.0.1_202607")

import subprocess
import os
import sys
import argparse
def read_requirements(requirements_file):
    with open(requirements_file, 'r', encoding='utf-16') as f:
        while f.readline():
            yield f.readline().strip()
def main():
    parser = argparse.ArgumentParser(description='Add python packages to uv')
    parser.add_argument('--requirements',"-r", help='Path to the requirements file', required=True)
    args = parser.parse_args()
    for package in read_requirements(args.requirements):
        subprocess.run(['uv', 'add', package])

if __name__ == "__main__":
    main()