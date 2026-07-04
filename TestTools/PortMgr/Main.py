import sys
import psutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QMessageBox, QHeaderView, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction


class PortManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("端口管理器 - 本地端口占用检测")
        self.setMinimumSize(900, 500)

        # 中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 顶部工具栏
        top_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("输入端口号过滤，例如 8080")
        self.filter_btn = QPushButton("过滤")
        self.clear_filter_btn = QPushButton("清除过滤")
        self.refresh_btn = QPushButton("刷新")
        
        # 新增：删除按钮
        self.delete_btn = QPushButton("删除占用进程")
        self.delete_btn.setEnabled(False)   # 初始禁用
        self.delete_btn.clicked.connect(self.on_delete_clicked)

        top_layout.addWidget(QLabel("端口过滤:"))
        top_layout.addWidget(self.filter_input)
        top_layout.addWidget(self.filter_btn)
        top_layout.addWidget(self.clear_filter_btn)
        top_layout.addStretch()
        top_layout.addWidget(self.delete_btn)   # 添加删除按钮
        top_layout.addWidget(self.refresh_btn)

        layout.addLayout(top_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["协议", "本地端口", "状态", "PID", "进程名称", "连接详情"])
        # 修复：使用 QHeaderView.ResizeMode.Stretch
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        # 连接选择变化信号，控制删除按钮的启用状态
        self.table.itemSelectionChanged.connect(self.update_delete_button_state)

        layout.addWidget(self.table)

        # 状态栏
        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

        # 连接信号
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.filter_btn.clicked.connect(self.apply_filter)
        self.clear_filter_btn.clicked.connect(self.clear_filter)

        # 数据缓存
        self.all_connections = []   # 存储原始数据（每条为dict）
        self.current_filter_port = None

        # 初次加载
        self.refresh_data()

    def get_connections(self):
        """获取所有网络连接信息"""
        connections = []
        try:
            net_cons = psutil.net_connections()
        except Exception as e:
            self.status_label.setText(f"获取连接失败: {e} (可能需要管理员权限)")
            return connections

        for conn in net_cons:
            if conn.laddr and conn.laddr.port:
                port = conn.laddr.port
                proto = "TCP" if conn.type == psutil.socket.SOCK_STREAM else "UDP" if conn.type == psutil.socket.SOCK_DGRAM else "?"
                status = conn.status if conn.status else "无状态"
                pid = conn.pid
                pname = ""
                if pid and pid != -1:
                    try:
                        proc = psutil.Process(pid)
                        pname = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pname = "未知进程"

                remote = ""
                if conn.raddr:
                    remote = f"{conn.raddr.ip}:{conn.raddr.port}"
                else:
                    remote = "*:*"
                conn_detail = f"{conn.laddr.ip}:{port} -> {remote}"

                connections.append({
                    'proto': proto,
                    'port': port,
                    'status': status,
                    'pid': pid if pid and pid != -1 else None,
                    'pname': pname,
                    'conn': conn_detail
                })
        return connections

    def refresh_data(self):
        """刷新并显示所有连接"""
        self.status_label.setText("正在获取端口占用信息...")
        QApplication.processEvents()
        self.all_connections = self.get_connections()
        self.current_filter_port = None
        self.filter_input.clear()
        self.display_connections(self.all_connections)
        self.status_label.setText(f"获取完成，共 {len(self.all_connections)} 条连接")
        self.update_delete_button_state()  # 刷新后检查选中状态

    def display_connections(self, connections):
        """在表格中显示连接列表"""
        self.table.setRowCount(len(connections))
        for row, conn in enumerate(connections):
            proto_item = QTableWidgetItem(conn['proto'])
            port_item = QTableWidgetItem(str(conn['port']))
            status_item = QTableWidgetItem(conn['status'])
            pid_item = QTableWidgetItem(str(conn['pid']) if conn['pid'] else "-")
            pname_item = QTableWidgetItem(conn['pname'] if conn['pname'] else "-")
            detail_item = QTableWidgetItem(conn['conn'])

            for item in (proto_item, port_item, status_item, pid_item, pname_item, detail_item):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, proto_item)
            self.table.setItem(row, 1, port_item)
            self.table.setItem(row, 2, status_item)
            self.table.setItem(row, 3, pid_item)
            self.table.setItem(row, 4, pname_item)
            self.table.setItem(row, 5, detail_item)

    def apply_filter(self):
        """根据输入的端口号过滤显示"""
        port_str = self.filter_input.text().strip()
        if not port_str:
            self.clear_filter()
            return
        try:
            port = int(port_str)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "端口号必须是数字")
            return

        self.current_filter_port = port
        filtered = [conn for conn in self.all_connections if conn['port'] == port]
        if not filtered:
            QMessageBox.information(self, "无结果", f"未找到占用端口 {port} 的连接")
            self.display_connections([])
            self.status_label.setText(f"过滤端口 {port} -> 0 条记录")
        else:
            self.display_connections(filtered)
            self.status_label.setText(f"过滤端口 {port} -> {len(filtered)} 条记录")
        self.update_delete_button_state()

    def clear_filter(self):
        """清除过滤，显示所有连接"""
        self.current_filter_port = None
        self.filter_input.clear()
        self.display_connections(self.all_connections)
        self.status_label.setText(f"显示全部，共 {len(self.all_connections)} 条连接")
        self.update_delete_button_state()

    def update_delete_button_state(self):
        """根据表格是否有选中行来启用/禁用删除按钮"""
        has_selection = len(self.table.selectedItems()) > 0
        # 如果表格有选中行，按钮启用；否则禁用
        self.delete_btn.setEnabled(has_selection)

    def on_delete_clicked(self):
        """删除按钮点击事件：获取当前选中行的PID并结束进程"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        pid_item = self.table.item(current_row, 3)
        if not pid_item:
            return
        pid_str = pid_item.text()
        if pid_str == "-" or not pid_str:
            QMessageBox.warning(self, "无法删除", "此连接没有对应的 PID 或进程已不存在")
            return
        pid = int(pid_str)
        pname_item = self.table.item(current_row, 4)
        pname = pname_item.text() if pname_item else "未知进程"
        self.kill_process(pid, pname)

    def show_context_menu(self, pos):
        """右键菜单：结束进程"""
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        pid_item = self.table.item(row, 3)
        pid_str = pid_item.text()
        if pid_str == "-" or not pid_str:
            QMessageBox.warning(self, "无法结束", "此连接没有对应的 PID 或进程已不存在")
            return

        pid = int(pid_str)
        pname = self.table.item(row, 4).text()

        menu = QMenu()
        kill_action = QAction(f"结束进程 {pname} (PID: {pid})", self)
        kill_action.triggered.connect(lambda: self.kill_process(pid, pname))
        menu.addAction(kill_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def kill_process(self, pid, pname):
        """结束指定 PID 的进程（需确认）"""
        reply = QMessageBox.question(
            self, "确认结束进程",
            f"确定要结束进程 \"{pname}\" (PID: {pid}) 吗？\n该操作会释放相关端口，但可能导致数据丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, "错误", "进程已不存在")
        except psutil.AccessDenied:
            QMessageBox.warning(self, "权限不足", "无法结束该进程，请尝试以管理员/root权限运行本程序")
        except psutil.TimeoutExpired:
            try:
                proc.kill()
                QMessageBox.information(self, "提示", f"进程 {pname} (PID: {pid}) 已被强制结束")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"强制结束失败: {e}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"结束进程失败: {e}")
        else:
            QMessageBox.information(self, "成功", f"已发送终止信号给进程 {pname} (PID: {pid})")
            self.refresh_data()


def main():
    app = QApplication(sys.argv)
    window = PortManager()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()