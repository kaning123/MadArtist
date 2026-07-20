#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import os
import shutil
import logging
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager

from PyQt6.QtCore import (
    QAbstractItemModel, QModelIndex, Qt, QVariant, QMimeData,
    QByteArray, QDataStream, QIODevice, QRegularExpression, pyqtSlot
)
from PyQt6.QtWidgets import (
    QApplication, QDialog, QTreeView, QWidget, QVBoxLayout,
    QPushButton, QMessageBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QStyledItemDelegate, QFileDialog, QMenu, QInputDialog,
    QHBoxLayout, QLabel, QToolBar, QStatusBar, QMenuBar
)
from PyQt6.QtGui import QBrush, QColor, QAction, QUndoCommand, QUndoStack

# Rich 日志设置
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("JsonEditor")

# ---------- 配置文件路径 ----------
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "Config", "Default.json")
try:
    with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
        DEFAULT_SAMPLE_JSON = json.load(f)
except Exception as e:
    logger.error(f"无法加载默认配置: {e}")
    DEFAULT_SAMPLE_JSON = {}


# ---------- 上下文管理器：批量更新模型 ----------
@contextmanager
def batch_update_model(model: QAbstractItemModel):
    """暂停模型信号，退出时发出 layoutChanged 以批量刷新"""
    model.layoutAboutToBeChanged.emit()
    try:
        yield
    finally:
        model.layoutChanged.emit()


# ---------- 撤销命令 ----------
class EditCommand(QUndoCommand):
    def __init__(self, model, before, after, description: str, parent=None):
        super().__init__(description, parent)
        self.model = model
        self.before = before
        self.after = after

    def undo(self):
        with batch_update_model(self.model):
            self.model.restore_state(self.before)

    def redo(self):
        with batch_update_model(self.model):
            self.model.restore_state(self.after)


class JsonNode:
    """JSON 树节点"""
    def __init__(self, key: Any, value: Any, parent: Optional['JsonNode'] = None):
        self.key = key
        self.value = value
        self.parent = parent
        self.children: list[JsonNode] = []
        self._build_children()

    def _build_children(self):
        self.children.clear()
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
        self._highlight_keys: set = set()   # 高亮键对应的键名
        self._highlight_vals: dict = {}     # {节点key: (列, ...)} 存储需要高亮的节点和列
        # 简单实现：存储匹配值的节点key，在 data 中判断列
        self._highlight_val_keys: set = set()  # 节点key（用于值列高亮）

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
            # 高亮：键列匹配键搜索，值列匹配值搜索
            if index.column() == 0 and node.key in self._highlight_keys:
                return QBrush(QColor(255, 255, 150))
            if index.column() == 1 and node.key in self._highlight_val_keys:
                return QBrush(QColor(200, 255, 200))
        return QVariant()

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        node = index.internalPointer()
        before = self._capture_state()

        if index.column() == 0:   # 修改键
            if node.parent and isinstance(node.parent.value, list):
                return False
            old_key = node.key
            if old_key == value:
                return False
            if node.parent and isinstance(node.parent.value, dict):
                if value in node.parent.value:
                    logger.warning(f"键 '{value}' 已存在")
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
            # 若类型变化，重建子节点
            if isinstance(old_val, (dict, list)) != isinstance(new_val, (dict, list)):
                node.children.clear()
                if isinstance(new_val, (dict, list)):
                    node._build_children()

        after = self._capture_state()
        cmd = EditCommand(self, before, after, f"修改 {node.key}")
        self.undo_stack.push(cmd)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        logger.info(f"修改节点: {node.key}")
        return True

    def _convert_value(self, raw: Any) -> Any:
        """将输入转换为合适的 Python 类型"""
        if not isinstance(raw, str):
            return raw
        low = raw.strip().lower()
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
        node = index.internalPointer()
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | \
                Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled
        if not node.is_container():
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return ["键", "值"][section]
        return QVariant()

    # ---------- 拖放支持（仅复制）----------
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
        if action == Qt.DropAction.MoveAction:
            # 仅支持复制，移动操作忽略（避免源节点丢失）
            return False
        if not data.hasFormat("application/x-jsonnode"):
            return False
        stream = QDataStream(data.data("application/x-jsonnode"), QIODevice.OpenModeFlag.ReadOnly)
        node_data = json.loads(stream.readQString())
        new_node = JsonNode(node_data["key"], node_data["value"])
        target_parent = parent.internalPointer() if parent.isValid() else self.root_node
        if not isinstance(target_parent.value, (dict, list)):
            return False
        before = self._capture_state()

        if isinstance(target_parent.value, dict):
            if new_node.key in target_parent.value:
                logger.warning(f"拖放失败：键 '{new_node.key}' 已存在")
                return False
            target_parent.value[new_node.key] = new_node.value
            new_node.parent = target_parent
            target_parent.children.append(new_node)
        else:  # list
            if row < 0 or row > len(target_parent.value):
                row = len(target_parent.value)
            target_parent.value.insert(row, new_node.value)
            new_node.key = row
            new_node.parent = target_parent
            target_parent.children.insert(row, new_node)
            # 更新后续子节点的索引
            for i in range(row + 1, len(target_parent.children)):
                target_parent.children[i].key = i

        after = self._capture_state()
        cmd = EditCommand(self, before, after, "粘贴节点（拖放）")
        self.undo_stack.push(cmd)
        # 强制刷新视图
        self.beginResetModel()
        self.endResetModel()
        logger.info(f"拖放节点到 {target_parent.key}")
        return True

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction  # 只允许复制，防止移动导致数据丢失

    # ---------- 撤销状态保存/恢复 ----------
    def _capture_state(self):
        return json.loads(json.dumps(self.root_node.value, default=str))

    def restore_state(self, state):
        self.root_node.value = state
        self.root_node.children.clear()
        self.root_node._build_children()

    # ---------- 对外接口 ----------
    def add_dict_item(self, parent_node, key, value):
        before = self._capture_state()
        parent_node.value[key] = value
        new_child = JsonNode(key, value, parent_node)
        parent_node.children.append(new_child)
        after = self._capture_state()
        cmd = EditCommand(self, before, after, f"添加键 {key}")
        self.undo_stack.push(cmd)
        self.layoutChanged.emit()
        logger.info(f"添加字典项: {key}")

    def add_list_item(self, parent_node, value):
        before = self._capture_state()
        parent_node.value.append(value)
        new_idx = len(parent_node.value) - 1
        new_child = JsonNode(new_idx, value, parent_node)
        parent_node.children.append(new_child)
        after = self._capture_state()
        cmd = EditCommand(self, before, after, "添加列表项")
        self.undo_stack.push(cmd)
        self.layoutChanged.emit()
        logger.info("添加列表项")

    def delete_node(self, node):
        before = self._capture_state()
        parent_node = node.parent
        if parent_node is None:
            return
        if isinstance(parent_node.value, dict):
            del parent_node.value[node.key]
        elif isinstance(parent_node.value, list):
            parent_node.value.pop(node.key)
            # 重新索引后续节点
            for i, child in enumerate(parent_node.children):
                child.key = i
        parent_node.children.remove(node)
        after = self._capture_state()
        cmd = EditCommand(self, before, after, f"删除 {node.key}")
        self.undo_stack.push(cmd)
        self.layoutChanged.emit()
        logger.info(f"删除节点: {node.key}")


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
            # null 或其他类型使用可编辑文本框
            le = QLineEdit(parent)
            le.setText(str(val) if val is not None else "null")
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
            else:
                editor.setText(str(val) if val is not None else "null")
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
                # 允许从 null 改为其他类型
                text = editor.text()
                new_val = model._convert_value(text)
            else:
                new_val = model._convert_value(editor.text())
            model.setData(index, new_val, Qt.ItemDataRole.EditRole)
        else:
            new_key = editor.text()
            model.setData(index, new_key, Qt.ItemDataRole.EditRole)


class JsonEditorWindow(QDialog):
    def __init__(self,
                 title: str = "MadArtist JSON Editor - Version Alpha_v0.0.2_202607",
                 config_json: dict = None,
                 enable_acts: bool = False,
                 enable_btns: bool = False,
                 quit_with_save: bool = False):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(950, 750)

        self.quit_with_save = quit_with_save
        self.current_file_path: Optional[str] = None  # 跟踪当前文件路径
        self.undo_stack = QUndoStack(self)
        self.root = JsonNode("root", config_json or DEFAULT_SAMPLE_JSON)
        self.model = JsonModel(self.root, self.undo_stack, self)

        # 中央树形视图
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

        # ---------- 菜单栏 ----------
        menubar = QMenuBar(self)
        file_menu = menubar.addMenu("文件(&F)")
        load_action = QAction("加载 JSON...", self, triggered=self.load_json)
        load_action.setShortcut("Ctrl+O")
        file_menu.addAction(load_action)
        save_action = QAction("保存 JSON", self, triggered=self.save_json)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        save_as_action = QAction("另存为...", self, triggered=self.save_json_as)
        save_as_action.setShortcut("Ctrl+Shift+S")
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        exit_action = QAction("退出", self, triggered=self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("编辑(&E)")
        undo_action = self.undo_stack.createUndoAction(self, "撤销")
        undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(undo_action)
        redo_action = self.undo_stack.createRedoAction(self, "重做")
        redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        cut_action = QAction("剪切", self, triggered=self.cut_node)
        cut_action.setShortcut("Ctrl+X")
        edit_menu.addAction(cut_action)
        copy_action = QAction("复制", self, triggered=self.copy_node)
        copy_action.setShortcut("Ctrl+C")
        edit_menu.addAction(copy_action)
        paste_action = QAction("粘贴", self, triggered=self.paste_node)
        paste_action.setShortcut("Ctrl+V")
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        del_action = QAction("删除", self, triggered=self.delete_item)
        del_action.setShortcut("Del")
        edit_menu.addAction(del_action)

        for act in (cut_action, copy_action, paste_action, del_action, load_action, save_action, save_as_action):
            act.setEnabled(enable_acts)

        # ---------- 工具栏 ----------
        tb = QToolBar(self)
        tb.addAction(undo_action)
        tb.addAction(redo_action)

        # ---------- 状态栏 ----------
        self.status_bar = QStatusBar(self)
        self.undo_stack.indexChanged.connect(self._update_status)
        self._update_status()

        # ---------- 按钮区域 ----------
        btn_undo = QPushButton("↩ 撤销")
        btn_undo.clicked.connect(self.undo_stack.undo)
        btn_undo.setEnabled(False)
        self.undo_stack.canUndoChanged.connect(btn_undo.setEnabled)

        btn_redo = QPushButton("↪ 重做")
        btn_redo.clicked.connect(self.undo_stack.redo)
        btn_redo.setEnabled(False)
        self.undo_stack.canRedoChanged.connect(btn_redo.setEnabled)

        btn_load = QPushButton("加载 JSON")
        btn_save = QPushButton("保存 JSON")
        btn_add_dict = QPushButton("添加字典键")
        btn_add_list = QPushButton("添加列表项")
        btn_del = QPushButton("删除节点")
        btn_copy = QPushButton("复制节点")
        btn_paste = QPushButton("粘贴节点")
        btn_cut = QPushButton("剪切节点")

        for btn in (btn_load, btn_save, btn_add_dict, btn_add_list,
                    btn_del, btn_copy, btn_paste, btn_cut):
            btn.setEnabled(enable_btns)

        btn_layout = QHBoxLayout()
        for btn in (btn_undo, btn_redo, btn_load, btn_save, btn_add_dict,
                    btn_add_list, btn_del, btn_copy, btn_paste, btn_cut):
            btn_layout.addWidget(btn)
        btn_layout.addStretch()

        # 搜索栏布局
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("🔍 搜索:"))
        top_layout.addWidget(self.search_edit)

        # ---------- 整体布局 ----------
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(menubar)
        main_layout.addWidget(tb)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.tree)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.status_bar)

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

    @pyqtSlot()
    def _update_status(self):
        text = self.undo_stack.undoText()
        if text:
            self.status_bar.showMessage(f"最后操作: {text}")
        else:
            self.status_bar.showMessage("就绪")

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
            self.clipboard_data = json.loads(json.dumps({"key": node.key, "value": node.value}, default=str))
            self.status_bar.showMessage(f"已复制 {node.key}", 3000)
            logger.info(f"复制节点: {node.key}")

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
            new_node.parent = target
            target.children.append(new_node)
        else:
            target.value.append(new_node.value)
            new_node.key = len(target.value) - 1
            new_node.parent = target
            target.children.append(new_node)
        after = self.model._capture_state()
        cmd = EditCommand(self.model, before, after, "粘贴节点")
        self.undo_stack.push(cmd)
        self.tree.expand(self.tree.currentIndex())
        self.status_bar.showMessage("粘贴成功", 3000)
        logger.info("粘贴节点")

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
            self.current_file_path = path  # 记录路径
            self.setWindowTitle(f"{os.path.basename(path)} - {self.windowTitle().split(' - ')[-1]}")
            self.status_bar.showMessage(f"已加载 {path}", 5000)
            logger.info(f"加载文件: {path}")
        except PermissionError:
            QMessageBox.critical(self, "权限错误", f"没有读取权限: {path}")
            logger.exception("权限错误")
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON 解析错误", f"无效的 JSON 格式:\n{e}")
            logger.exception("JSON 解析错误")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            logger.exception("加载文件异常")

    def save_json(self):
        """保存到当前文件，若无则调用另存为"""
        if self.current_file_path:
            self._save_to_path(self.current_file_path)
        else:
            self.save_json_as()

    def save_json_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存 JSON", self.current_file_path or "", "JSON (*.json)")
        if not path:
            return
        self._save_to_path(path)

    def _save_to_path(self, path: str):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.root.value, f, indent=2, ensure_ascii=False)
            self.current_file_path = path
            self.setWindowTitle(f"{os.path.basename(path)} - {self.windowTitle().split(' - ')[-1]}")
            self.status_bar.showMessage(f"已保存 {path}", 5000)
            logger.info(f"保存文件: {path}")
        except PermissionError:
            QMessageBox.critical(self, "权限错误", f"没有写入权限: {path}")
            logger.exception("权限错误")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
            logger.exception("保存文件异常")

    def highlight_search(self, pattern):
        self.model._highlight_keys.clear()
        self.model._highlight_val_keys.clear()
        if not pattern:
            self.tree.viewport().update()
            return
        regex = QRegularExpression(pattern)
        regex.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)

        def collect(node):
            if regex.match(str(node.key)).hasMatch():
                self.model._highlight_keys.add(node.key)
            if not node.is_container() and regex.match(str(node.value)).hasMatch():
                self.model._highlight_val_keys.add(node.key)
            for ch in node.children:
                collect(ch)

        collect(self.root)
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

    def to_dict(self):
        return self.root.value.copy() if isinstance(self.root.value, dict) else self.root.value

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "退出", "是否保存更改？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.quit_with_save:
                self.save_json()
            self.accept()
        elif reply == QMessageBox.StandardButton.No:
            self.reject()
        else:  # Cancel
            event.ignore()


# ---------- 辅助函数 ----------
def get_my_dir():
    return os.path.dirname(os.path.abspath(__file__))

def create_dir(path: Path, overwrite=False) -> bool:
    try:
        path = Path(path)
        if overwrite and path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {path}, 错误: {e}")
        return False

def file_exists(path: Path):
    return Path(path).exists()