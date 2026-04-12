import Tools.file_lib as fl
import os

ROOT_DIR = fl.get_parent_dir(fl.get_my_dir())
UI_DIR = os.path.join(ROOT_DIR, 'qt_ui')
PY_DIR = os.path.join(ROOT_DIR, 'py_ui')

def list_ui_files(ui_dir = UI_DIR):
    return [f for f in os.listdir(ui_dir) if f.endswith('.ui')]

def convert_ui_to_py():
    for ui_file in list_ui_files():
        py_file = os.path.splitext(ui_file)[0] + '.py'
        cmd = f'pyuic6 -o {str(fl.merge_dir_txt2(PY_DIR, py_file))} {str(fl.merge_dir_txt2(UI_DIR, ui_file))}'
        print(cmd)
        os.system(cmd)
    print(f'Converted: {ui_file} -> {py_file}')

if __name__ == "__main__":
    convert_ui_to_py()