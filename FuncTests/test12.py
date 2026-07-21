#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from typing import Any
from PyQt6.QtCore import (
    QAbstractItemModel, QModelIndex, Qt, QVariant, QMimeData,
    QByteArray, QDataStream, QIODevice, QRegularExpression
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QWidget, QVBoxLayout,
    QPushButton, QMessageBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QStyledItemDelegate, QFileDialog, QMenu, QInputDialog,
    QHBoxLayout, QLabel, QToolBar
)
from PyQt6.QtGui import QBrush, QColor, QAction, QUndoCommand, QUndoStack


# ---------- 撤销命令 ----------
class EditCommand(QUndoCommand):
    def __init__(self, model, before, after, description: str, parent=None):
        super().__init__(description, parent)
        self.model = model
        self.before = before
        self.after = after

    def undo(self):
        self.model.restore_state(self.before)

    def redo(self):
        self.model.restore_state(self.after)


class JsonNode:
    """JSON 树节点"""
    def __init__(self, key: Any, value: Any, parent=None):
        self.key = key
        self.value = value
        self.parent = parent
        self.children = []
        self._build_children()

    def _build_children(self):
        if isinstance(self.value, dict):
            for k, v in self.value.items():
                self.children.append(JsonNode(k, v, self))
        elif isinstance(self.value, list):
            for idx, v in enumerate(self.value):
                self.children.append(JsonNode(idx, v, self))

    def is_container(self) -> bool:
        return isinstance(self.value, (dict, list))

    def row(self) -> int:
        if self.parent:
            return self.parent.children.index(self)
        return 0


class JsonModel(QAbstractItemModel):
    def __init__(self, root_node: JsonNode, undo_stack: QUndoStack, parent=None):
        super().__init__(parent)
        self.root_node = root_node
        self.undo_stack = undo_stack
        self._highlight_keys = set()
        self._highlight_values = set()

    # ---------- 必要虚函数 ----------
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_node = parent.internalPointer() if parent.isValid() else self.root_node
        if row < len(parent_node.children):
            return self.createIndex(row, column, parent_node.children[row])
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        parent_node = node.parent
        if parent_node == self.root_node or parent_node is None:
            return QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:
            return 0
        node = parent.internalPointer() if parent.isValid() else self.root_node
        return len(node.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()
        node = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if index.column() == 0:
                return str(node.key) if node.key is not None else ""
            else:
                if isinstance(node.value, dict):
                    return "{...}" if node.value else "{}"
                elif isinstance(node.value, list):
                    return "[...]" if node.value else "[]"
                else:
                    return str(node.value) if node.value is not None else "null"
        elif role == Qt.ItemDataRole.BackgroundRole:
            if node.key in self._highlight_keys:
                return QBrush(QColor(255, 255, 150))
            if node.key in self._highlight_values:
                return QBrush(QColor(200, 255, 200))
        return QVariant()

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        node = index.internalPointer()
        before = self._capture_state()
        if index.column() == 0:   # 修改键
            old_key = node.key
            if old_key == value:
                return False
            if node.parent and isinstance(node.parent.value, dict):
                if value in node.parent.value:
                    return False
                node.parent.value[value] = node.parent.value.pop(old_key)
                node.key = value
        else:                      # 修改值
            new_val = self._convert_value(value)
            old_val = node.value
            node.value = new_val
            # 更新父容器中的引用
            if node.parent:
                if isinstance(node.parent.value, dict):
                    node.parent.value[node.key] = new_val
                elif isinstance(node.parent.value, list):
                    node.parent.value[node.key] = new_val
            # 若类型从容器变成非容器，或相反，需重建子节点
            if isinstance(old_val, (dict, list)) != isinstance(new_val, (dict, list)):
                node.children.clear()
                if isinstance(new_val, (dict, list)):
                    node._build_children()
        after = self._capture_state()
        cmd = EditCommand(self, before, after, f"修改 {node.key}")
        self.undo_stack.push(cmd)
        # 刷新显示（简单但有效）
        self.beginResetModel()
        self.endResetModel()
        return True

    def _convert_value(self, raw: str) -> Any:
        low = raw.lower()
        if low == "null":
            return None
        if low == "true":
            return True
        if low == "false":
            return False
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        return raw

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled |
                Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsDragEnabled |
                Qt.ItemFlag.ItemIsDropEnabled)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return ["键", "值"][section]
        return QVariant()

    # ---------- 拖放支持 ----------
    def mimeTypes(self):
        return ["application/x-jsonnode"]

    def mimeData(self, indexes):
        if not indexes:
            return None
        node = indexes[0].internalPointer()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.OpenModeFlag.WriteOnly)
        stream.writeQString(json.dumps({"key": node.key, "value": node.value}, ensure_ascii=False))
        mime = QMimeData()
        mime.setData("application/x-jsonnode", data)
        return mime

    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat("application/x-jsonnode"):
            return False
        stream = QDataStream(data.data("application/x-jsonnode"), QIODevice.OpenModeFlag.ReadOnly)
        node_data = json.loads(stream.readQString())
        new_node = JsonNode(node_data["key"], node_data["value"])
        target_parent = parent.internalPointer() if parent.isValid() else self.root_node
        if not isinstance(target_parent.value, (dict, list)):
            return False
        # 记录之前状态
        before = self._capture_state()
        if isinstance(target_parent.value, dict):
            if new_node.key in target_parent.value:
                return False
            target_parent.value[new_node.key] = new_node.value
        else:  # list
            if row < 0:
                row = len(target_parent.value)
            target_parent.value.insert(row, new_node.value)
            new_node.key = row
        new_node.parent = target_parent
        target_parent.children.append(new_node)
        after = self._capture_state()
        cmd = EditCommand(self, before, after, "粘贴节点")
        self.undo_stack.push(cmd)
        self.beginResetModel()
        self.endResetModel()
        return True

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    # ---------- 撤销状态保存/恢复 ----------
    def _capture_state(self):
        return json.loads(json.dumps(self.root_node.value))

    def restore_state(self, state):
        self.root_node.value = state
        self.beginResetModel()
        self.root_node.children.clear()
        self.root_node._build_children()
        self.endResetModel()

    # ---------- 对外接口 ----------
    def add_dict_item(self, parent_node, key, value):
        before = self._capture_state()
        parent_node.value[key] = value
        new_child = JsonNode(key, value, parent_node)
        parent_node.children.append(new_child)
        after = self._capture_state()
        cmd = EditCommand(self, before, after, f"添加键 {key}")
        self.undo_stack.push(cmd)
        self.beginResetModel()
        self.endResetModel()

    def add_list_item(self, parent_node, value):
        before = self._capture_state()
        parent_node.value.append(value)
        new_idx = len(parent_node.value) - 1
        new_child = JsonNode(new_idx, value, parent_node)
        parent_node.children.append(new_child)
        after = self._capture_state()
        cmd = EditCommand(self, before, after, "添加列表项")
        self.undo_stack.push(cmd)
        self.beginResetModel()
        self.endResetModel()

    def delete_node(self, node):
        before = self._capture_state()
        parent_node = node.parent
        if parent_node is None:
            return
        if isinstance(parent_node.value, dict):
            del parent_node.value[node.key]
        elif isinstance(parent_node.value, list):
            parent_node.value.pop(node.key)
            # 后续节点重新索引
            for i, child in enumerate(parent_node.children):
                if child.key > node.key:
                    child.key = i
        parent_node.children.remove(node)
        after = self._capture_state()
        cmd = EditCommand(self, before, after, f"删除 {node.key}")
        self.undo_stack.push(cmd)
        self.beginResetModel()
        self.endResetModel()


class JsonDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        if index.column() == 1:
            node = index.internalPointer()
            val = node.value
            if isinstance(val, bool):
                cb = QComboBox(parent)
                cb.addItems(["true", "false"])
                cb.setCurrentText("true" if val else "false")
                return cb
            if isinstance(val, int):
                sb = QSpinBox(parent)
                sb.setRange(-10**9, 10**9)
                sb.setValue(val)
                return sb
            if isinstance(val, float):
                sb = QDoubleSpinBox(parent)
                sb.setRange(-10**9, 10**9)
                sb.setValue(val)
                return sb
            if val is None:
                cb = QComboBox(parent)
                cb.addItems(["null"])
                return cb
            le = QLineEdit(parent)
            le.setText(str(val))
            return le
        else:
            le = QLineEdit(parent)
            le.setText(str(index.internalPointer().key))
            return le

    def setEditorData(self, editor, index):
        if index.column() == 1:
            val = index.internalPointer().value
            if isinstance(val, bool):
                editor.setCurrentText("true" if val else "false")
            elif isinstance(val, (int, float)):
                editor.setValue(val)
            elif val is None:
                editor.setCurrentText("null")
            else:
                editor.setText(str(val))
        else:
            editor.setText(str(index.internalPointer().key))

    def setModelData(self, editor, model, index):
        if index.column() == 1:
            node = index.internalPointer()
            if isinstance(node.value, bool):
                new_val = editor.currentText() == "true"
            elif isinstance(node.value, (int, float)):
                new_val = editor.value()
            elif node.value is None:
                new_val = None
            else:
                new_val = editor.text()
            model.setData(index, new_val, Qt.ItemDataRole.EditRole)
        else:
            new_key = editor.text()
            model.setData(index, new_key, Qt.ItemDataRole.EditRole)


class JsonEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 JSON 编辑器 - 完整功能版")
        self.resize(950, 750)

        self.undo_stack = QUndoStack(self)
        sample = {
            "name": "Alice",
            "age": 30,
            "address": {"city": "Beijing", "zip": 100000},
            "hobbies": ["reading", "swimming"],
            "active": True,
            "null_field": None
        }
        self.root = JsonNode("root", sample)
        self.model = JsonModel(self.root, self.undo_stack, self)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setItemDelegate(JsonDelegate(self))
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.setColumnWidth(0, 250)

        # 搜索栏
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("正则搜索 (键/值高亮)")
        self.search_edit.textChanged.connect(self.highlight_search)

        # 工具栏
        tb = self.addToolBar("编辑")
        tb.addAction(self.undo_stack.createUndoAction(self, "撤销"))
        tb.addAction(self.undo_stack.createRedoAction(self, "重做"))
        tb.addSeparator()

        # 按钮
        btn_load = QPushButton("加载 JSON")
        btn_save = QPushButton("保存 JSON")
        btn_add_dict = QPushButton("添加字典键")
        btn_add_list = QPushButton("添加列表项")
        btn_del = QPushButton("删除节点")
        btn_copy = QPushButton("复制节点")
        btn_paste = QPushButton("粘贴节点")
        btn_cut = QPushButton("剪切节点")

        btn_layout = QHBoxLayout()
        for btn in (btn_load, btn_save, btn_add_dict, btn_add_list, btn_del, btn_copy, btn_paste, btn_cut):
            btn_layout.addWidget(btn)
        btn_layout.addStretch()

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("🔍 搜索:"))
        top_layout.addWidget(self.search_edit)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(top_layout)
        layout.addWidget(self.tree)
        layout.addLayout(btn_layout)
        self.setCentralWidget(central)

        # 信号连接
        btn_load.clicked.connect(self.load_json)
        btn_save.clicked.connect(self.save_json)
        btn_add_dict.clicked.connect(self.add_dict_item)
        btn_add_list.clicked.connect(self.add_list_item)
        btn_del.clicked.connect(self.delete_item)
        btn_copy.clicked.connect(self.copy_node)
        btn_paste.clicked.connect(self.paste_node)
        btn_cut.clicked.connect(self.cut_node)

        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        self.clipboard_data = None

    def current_node(self):
        idx = self.tree.currentIndex()
        return idx.internalPointer() if idx.isValid() else None

    def add_dict_item(self):
        node = self.current_node()
        if node is None or not isinstance(node.value, dict):
            QMessageBox.warning(self, "警告", "请选中一个字典节点")
            return
        key, ok = QInputDialog.getText(self, "添加键", "键名:")
        if not ok or not key:
            return
        if key in node.value:
            QMessageBox.warning(self, "错误", "键已存在")
            return
        val_str, ok = QInputDialog.getText(self, "添加值", "值 (自动类型):")
        if not ok:
            return
        val = self.model._convert_value(val_str)
        self.model.add_dict_item(node, key, val)
        self.tree.expand(self.tree.currentIndex())

    def add_list_item(self):
        node = self.current_node()
        if node is None or not isinstance(node.value, list):
            QMessageBox.warning(self, "警告", "请选中一个列表节点")
            return
        val_str, ok = QInputDialog.getText(self, "添加列表项", "值 (自动类型):")
        if not ok:
            return
        val = self.model._convert_value(val_str)
        self.model.add_list_item(node, val)
        self.tree.expand(self.tree.currentIndex())

    def delete_item(self):
        node = self.current_node()
        if node is None or node == self.root:
            QMessageBox.warning(self, "错误", "不能删除根节点")
            return
        self.model.delete_node(node)

    def copy_node(self):
        node = self.current_node()
        if node and node != self.root:
            self.clipboard_data = json.loads(json.dumps({"key": node.key, "value": node.value}))
            QMessageBox.information(self, "复制", f"已复制 {node.key}")

    def cut_node(self):
        self.copy_node()
        self.delete_item()

    def paste_node(self):
        if self.clipboard_data is None:
            QMessageBox.warning(self, "粘贴", "剪贴板为空")
            return
        target = self.current_node()
        if target is None:
            target = self.root
        if not isinstance(target.value, (dict, list)):
            QMessageBox.warning(self, "粘贴", "目标必须是字典或列表")
            return
        before = self.model._capture_state()
        new_node = JsonNode(self.clipboard_data["key"], self.clipboard_data["value"])
        if isinstance(target.value, dict):
            if new_node.key in target.value:
                QMessageBox.warning(self, "粘贴", f"键 '{new_node.key}' 已存在")
                return
            target.value[new_node.key] = new_node.value
        else:
            target.value.append(new_node.value)
            new_node.key = len(target.value) - 1
        new_node.parent = target
        target.children.append(new_node)
        after = self.model._capture_state()
        cmd = EditCommand(self.model, before, after, "粘贴节点")
        self.undo_stack.push(cmd)
        self.model.beginResetModel()
        self.model.endResetModel()
        self.tree.expand(self.tree.currentIndex())

    def load_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开 JSON", "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.root = JsonNode("root", data)
            self.model.beginResetModel()
            self.model.root_node = self.root
            self.model.endResetModel()
            self.undo_stack.clear()
            self.clipboard_data = None
            QMessageBox.information(self, "成功", f"已加载 {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def save_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存 JSON", "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.root.value, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "成功", f"已保存 {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def highlight_search(self, pattern):
        if not pattern:
            self.model._highlight_keys.clear()
            self.model._highlight_values.clear()
            self.tree.viewport().update()
            return
        regex = QRegularExpression(pattern)
        regex.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
        keys = set()
        vals = set()

        def collect(node):
            if regex.match(str(node.key)).hasMatch():
                keys.add(node.key)
            if not node.is_container() and regex.match(str(node.value)).hasMatch():
                vals.add(node.key)
            for ch in node.children:
                collect(ch)

        collect(self.root)
        self.model._highlight_keys = keys
        self.model._highlight_values = vals
        self.tree.viewport().update()

    def show_context_menu(self, pos):
        idx = self.tree.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu()
        menu.addAction("添加字典键", self.add_dict_item)
        menu.addAction("添加列表项", self.add_list_item)
        menu.addAction("删除", self.delete_item)
        menu.addSeparator()
        menu.addAction("复制", self.copy_node)
        menu.addAction("剪切", self.cut_node)
        menu.addAction("粘贴", self.paste_node)
        menu.exec(self.tree.viewport().mapToGlobal(pos))


def main():
    app = QApplication(sys.argv)
    win = JsonEditorWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()