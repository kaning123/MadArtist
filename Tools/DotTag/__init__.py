import os

def get_tags(dir_):
    for file in os.listdir(dir_):
        if file.endswith(".tag"):
            yield file.readlines()

def get_tag(f):
    with open(f, "r") as file:
        for line in file:
            yield line.strip()

def add_tag(f,tag):
    with open(f, "a") as file:
        file.writelines(tag)

def remove_tag(f,tag):
    with open(f, "r") as file:
        lines = file.readlines()
        lines = [line for line in lines if line.strip() != tag]
        with open(f, "w") as file:
            file.writelines(lines)