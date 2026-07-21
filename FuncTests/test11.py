#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
from typing import Any, Dict, List, Union

from PyQt6.QtCore import (
    QAbstractItemModel, QModelIndex, Qt, QVariant, QMimeData
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QWidget, QVBoxLayout,
    QPushButton, QMessageBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QStyledItemDelegate, QFileDialog, QMenu, QInputDialog
)
from PyQt6.QtGui import QIcon, QAction


# ---------- 树节点 ----------
class JsonNode:
    """表示 JSON 树中的一个节点"""
    def __init__(self, key: Any, value: Any, parent=None):
        self.key = key          # 键名（列表时为索引 int）
        self.value = value      # 值（可能是 dict/list 或基本类型）
        self.parent = parent
        self.children = []      # 子节点列表

        # 如果是容器（dict/list），递归构建子节点
        if isinstance(value, dict):
            for k, v in value.items():
                self.children.append(JsonNode(k, v, self))
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                self.children.append(JsonNode(idx, item, self))

    def is_container(self) -> bool:
        """是否是容器（dict 或 list）"""
        return isinstance(self.value, (dict, list))

    def row(self) -> int:
        """返回在父节点中的行号"""
        if self.parent:
            return self.parent.children.index(self)
        return 0

    def __repr__(self):
        return f"JsonNode(key={self.key}, value={self.value})"


# ---------- 自定义 Model ----------
class JsonModel(QAbstractItemModel):
    def __init__(self, root_node: JsonNode, parent=None):
        super().__init__(parent)
        self.root_node = root_node

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()

        if row < len(parent_node.children):
            child_node = parent_node.children[row]
            return self.createIndex(row, column, child_node)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        child_node = index.internalPointer()
        parent_node = child_node.parent
        if parent_node == self.root_node or parent_node is None:
            return QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()
        return len(parent_node.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2   # 第一列：键，第二列：值

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return QVariant()
        node = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if index.column() == 0:
                return str(node.key) if node.key is not None else ""
            else:  # column 1
                # 对于容器，显示类型提示
                if isinstance(node.value, dict):
                    return "{...}" if node.value else "{}"
                elif isinstance(node.value, list):
                    return "[...]" if node.value else "[]"
                else:
                    return str(node.value) if node.value is not None else "null"
        return QVariant()

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        node = index.internalPointer()
        if index.column() == 0:
            # 修改键名（注意：字典键名不能重复，需要处理）
            old_key = node.key
            # 检查父节点中是否已存在新键名
            parent_node = node.parent
            if parent_node and isinstance(parent_node.value, dict):
                if value in parent_node.value:
                    return False  # 键名冲突
                # 更新键
                node.key = value
                # 更新父节点字典中的键
                parent_node.value[value] = parent_node.value.pop(old_key)
                self.dataChanged.emit(index, index)
                return True
            else:
                return False
        else:
            # 修改值
            # 自动尝试转换类型（int/float/bool/str）
            converted = self._convert_value(value)
            old_value = node.value
            node.value = converted
            # 更新父节点容器中的值
            parent_node = node.parent
            if parent_node:
                if isinstance(parent_node.value, dict):
                    parent_node.value[node.key] = converted
                elif isinstance(parent_node.value, list):
                    parent_node.value[node.key] = converted
            # 如果原来是容器，修改后变成非容器，则需要清空子节点
            if isinstance(old_value, (dict, list)) and not isinstance(converted, (dict, list)):
                node.children.clear()
                # 通知移除了所有子节点
                self.beginRemoveRows(index, 0, len(node.children)-1)
                self.endRemoveRows()
            # 如果原来不是容器，修改后变成容器，需要重建子节点
            elif not isinstance(old_value, (dict, list)) and isinstance(converted, (dict, list)):
                self.beginInsertRows(index, 0, len(node.children)-1)
                # 重新构建子节点
                if isinstance(converted, dict):
                    for k, v in converted.items():
                        node.children.append(JsonNode(k, v, node))
                elif isinstance(converted, list):
                    for idx, v in enumerate(converted):
                        node.children.append(JsonNode(idx, v, node))
                self.endInsertRows()
            self.dataChanged.emit(index, index)
            return True

    def _convert_value(self, value: str) -> Any:
        """尝试将字符串转换为合适的类型"""
        # 处理 null/None
        if value.lower() == "null":
            return None
        # 处理布尔
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        # 处理整数
        try:
            return int(value)
        except ValueError:
            pass
        # 处理浮点数
        try:
            return float(value)
        except ValueError:
            pass
        # 默认字符串
        return value

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        # 都允许编辑
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return ["Key", "Value"][section]
        return QVariant()


# ---------- 委托：为不同数据类型提供不同编辑器 ----------
class JsonDelegate(QStyledItemDelegate):
    """第二列根据值类型弹出合适的编辑器"""
    def createEditor(self, parent, option, index):
        if index.column() == 1:
            node = index.internalPointer()
            value = node.value
            # 如果是容器，不允许直接编辑（需要双击展开后用按钮编辑）
            if isinstance(value, (dict, list)):
                return None
            # 根据值的类型选择编辑器
            if isinstance(value, bool):
                combo = QComboBox(parent)
                combo.addItems(["true", "false"])
                combo.setCurrentText("true" if value else "false")
                return combo
            elif isinstance(value, int):
                spin = QSpinBox(parent)
                spin.setRange(-2147483647, 2147483647)
                spin.setValue(value)
                return spin
            elif isinstance(value, float):
                spin = QDoubleSpinBox(parent)
                spin.setRange(-1e9, 1e9)
                spin.setDecimals(6)
                spin.setValue(value)
                return spin
            elif value is None:
                combo = QComboBox(parent)
                combo.addItems(["null"])
                combo.setCurrentText("null")
                return combo
            else:
                return QLineEdit(parent, text=str(value))
        else:
            # 编辑键名
            return QLineEdit(parent, text=node.key)

    def setEditorData(self, editor, index):
        if index.column() == 1:
            node = index.internalPointer()
            value = node.value
            if isinstance(value, bool):
                editor.setCurrentText("true" if value else "false")
            elif isinstance(value, (int, float)):
                editor.setValue(value)
            elif value is None:
                editor.setCurrentText("null")
            else:
                editor.setText(str(value))
        else:
            editor.setText(str(node.key))

    def setModelData(self, editor, model, index):
        if index.column() == 1:
            node = index.internalPointer()
            if isinstance(node.value, bool):
                new_value = editor.currentText() == "true"
            elif isinstance(node.value, (int, float)):
                new_value = editor.value()
            elif node.value is None:
                new_value = None
            else:
                new_value = editor.text()
            model.setData(index, new_value, Qt.ItemDataRole.EditRole)
        else:
            new_key = editor.text()
            model.setData(index, new_key, Qt.ItemDataRole.EditRole)


# ---------- 主窗口 ----------
class JsonEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 嵌套字典/JSON 编辑器")
        self.resize(800, 600)

        # 示例数据
        sample_data = {
            "name": "Alice",
            "age": 30,
            "address": {
                "city": "Beijing",
                "zip": 100000
            },
            "hobbies": ["reading", "swimming"],
            "active": True,
            "null_field": None
        }
        self.root_node = JsonNode("root", sample_data)
        self.model = JsonModel(self.root_node)

        # 设置视图
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setItemDelegate(JsonDelegate(self))
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)
        self.tree.setExpandsOnDoubleClick(True)
        # 列宽
        self.tree.setColumnWidth(0, 250)

        # 按钮
        btn_layout = QVBoxLayout()
        btn_load = QPushButton("加载 JSON 文件")
        btn_save = QPushButton("保存到 JSON 文件")
        btn_add = QPushButton("添加键值对")
        btn_del = QPushButton("删除当前项")
        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)

        # 主布局
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.addWidget(self.tree)
        main_layout.addLayout(btn_layout)
        self.setCentralWidget(central)

        # 信号连接
        btn_load.clicked.connect(self.load_json)
        btn_save.clicked.connect(self.save_json)
        btn_add.clicked.connect(self.add_item)
        btn_del.clicked.connect(self.delete_item)

        # 右键菜单
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

    def get_current_node(self):
        idx = self.tree.currentIndex()
        if idx.isValid():
            return idx.internalPointer()
        return None

    def add_item(self):
        """在当前选中节点下添加新键值对（仅当父节点是 dict 时）"""
        idx = self.tree.currentIndex()
        if not idx.isValid():
            # 没选中时添加到根节点
            parent_node = self.root_node
        else:
            node = idx.internalPointer()
            # 如果选中的是叶子，父节点就是其父节点
            if not node.is_container():
                parent_node = node.parent
            else:
                parent_node = node
        # 只有 dict 才能添加新键
        if parent_node is None or not isinstance(parent_node.value, dict):
            QMessageBox.warning(self, "警告", "只能在字典（对象）中添加键值对")
            return

        # 输入键名
        key, ok = QInputDialog.getText(self, "添加键", "请输入键名:")
        if not ok or not key:
            return
        # 检查键名是否已存在
        if key in parent_node.value:
            QMessageBox.warning(self, "错误", f"键 '{key}' 已存在")
            return

        # 输入初始值
        value, ok = QInputDialog.getText(self, "添加值", "请输入值 (null/true/false/数字/字符串):")
        if not ok:
            return
        # 转换类型
        converted = self.model._convert_value(value)

        # 开始插入
        parent_index = self.model.index(parent_node.row(), 0, self.model.parent(self.model.createIndex(parent_node.row(), 0, parent_node)))
        if not parent_index.isValid():
            parent_index = QModelIndex()
        row = len(parent_node.children)
        self.model.beginInsertRows(parent_index, row, row)
        new_node = JsonNode(key, converted, parent_node)
        parent_node.children.append(new_node)
        parent_node.value[key] = converted
        self.model.endInsertRows()
        self.tree.expand(parent_index)

    def delete_item(self):
        """删除当前选中的节点"""
        idx = self.tree.currentIndex()
        if not idx.isValid():
            return
        node = idx.internalPointer()
        if node == self.root_node:
            QMessageBox.warning(self, "错误", "不能删除根节点")
            return
        parent_node = node.parent
        if parent_node is None:
            return
        # 开始删除
        parent_index = self.model.index(parent_node.row(), 0, self.model.parent(self.model.createIndex(parent_node.row(), 0, parent_node)))
        row = node.row()
        self.model.beginRemoveRows(parent_index, row, row)
        # 从父节点的 children 中移除
        parent_node.children.pop(row)
        # 从父节点的 value 中移除
        if isinstance(parent_node.value, dict):
            del parent_node.value[node.key]
        elif isinstance(parent_node.value, list):
            parent_node.value.pop(node.key)
        self.model.endRemoveRows()

    def load_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "打开 JSON 文件", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 重建模型
            self.root_node = JsonNode("root", data)
            self.model.beginResetModel()
            self.model = JsonModel(self.root_node)
            self.tree.setModel(self.model)
            self.tree.setItemDelegate(JsonDelegate(self))
            self.model.endResetModel()
            self.tree.expandToDepth(1)
            QMessageBox.information(self, "成功", f"已加载 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {e}")

    def save_json(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存 JSON 文件", "", "JSON Files (*.json)")
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.root_node.value, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "成功", f"已保存到 {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def show_context_menu(self, pos):
        idx = self.tree.indexAt(pos)
        if not idx.isValid():
            return
        menu = QMenu()
        add_action = QAction("添加子项", self)
        add_action.triggered.connect(self.add_item)
        del_action = QAction("删除", self)
        del_action.triggered.connect(self.delete_item)
        menu.addAction(add_action)
        menu.addAction(del_action)
        menu.exec(self.tree.viewport().mapToGlobal(pos))


def main():
    app = QApplication(sys.argv)
    win = JsonEditorWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()