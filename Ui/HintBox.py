import PyQt6
from PyQt6 import QtCore, QtGui, QtWidgets
import py_ui.HintBoxWithList as HintBoxWithList
import Tools.time_lib as tl
import threading
ReturnCache = {}
POOL = set()
def get_unique_name(name):
    _id = 1
    if name not in POOL:
        POOL.add(name)
        return name
    while name in POOL:
        _id += 1
        name = f'{name}_{_id}'
    POOL.add(name)
    return name
class HintBox(QtWidgets.QDialog, HintBoxWithList.Ui_Dialog):
    def __init__(self, parent=None, title="", message="", list_items=[]):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(title)
        self.HintLabel.setText(message)
        self.List_Display.addItems(list_items)
        self.name = get_unique_name(title)
    def accept(self):
        ReturnCache[self.name] = True
        super().accept()
    def reject(self):
        ReturnCache[self.name] = False
        super().reject()

def HintBox_show(title="", message="", list_items=[],operation=None):
    Dialog = HintBox(title=title, message=message, list_items=list_items)
    ret = Dialog.exec()
    print(f"Dialog return: {ret}")
    print(f"ReturnCache: {ReturnCache}")
    if operation is not None:
        operation(title,message,list_items,ret)
    sys.exit(ret)
    return ReturnCache.pop(Dialog.name) ,ret
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    print(HintBox_show(title="Test", message="This is a test message", list_items=["Item1", "Item2", "Item3"]))
    sys.exit(app.exec())