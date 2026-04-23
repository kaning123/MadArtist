import PyQt6
from PyQt6 import QtCore, QtGui, QtWidgets
import py_ui.HintBoxWithList as HintBoxWithList
import Tools.time_lib as tl
import threading

__INNER_VERSION__ = "Alpha_0.0.1_202604"

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
        self.accept_ = False
    def accept(self):
        self.accept_ = True
        super().accept()
    def reject(self):
        self.accept_ = False
        super().reject()

def HintBox_show(title="", message="", list_items=[],operation=None):
    Dialog = HintBox(title=title, message=message, list_items=list_items)
    ret = Dialog.exec()
    return Dialog.accept_
