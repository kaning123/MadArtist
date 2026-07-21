import sys
import platform
import subprocess
import tempfile
import shlex
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QLineEdit, QLabel, QMessageBox, QHeaderView, QCheckBox
)
from PyQt6.QtCore import QProcess, Qt, QTimer, QFile
from PyQt6.QtGui import QCloseEvent


class ProcessManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("进程管理器 - 支持终端交互")
        self.setMinimumSize(900, 500)

        # 存储进程信息：
        # 对于后台模式：(QProcess, row, name, pid, command, log_path, mode="background")
        # 对于交互模式：(terminal_pid, row, name, command, mode="interactive")
        self.processes = []

        # 创建界面
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 启动区域
        launch_group = QWidget()
        launch_layout = QHBoxLayout(launch_group)
        self.program_path_edit = QLineEdit()
        self.program_path_edit.setPlaceholderText("可执行文件或脚本路径...")
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_program)
        self.args_edit = QLineEdit()
        self.args_edit.setPlaceholderText("命令行参数（可选）")
        self.interactive_cb = QCheckBox("交互模式（在新终端中运行，支持输入）")
        launch_btn = QPushButton("启动进程")
        launch_btn.clicked.connect(self.launch_process)

        launch_layout.addWidget(QLabel("程序:"))
        launch_layout.addWidget(self.program_path_edit)
        launch_layout.addWidget(browse_btn)
        launch_layout.addWidget(QLabel("参数:"))
        launch_layout.addWidget(self.args_edit)
        launch_layout.addWidget(self.interactive_cb)
        launch_layout.addWidget(launch_btn)

        # 进程列表表格（6列）
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["进程名称", "PID/终端ID", "状态", "启动命令", "终止", "终端输出"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        terminate_btn = QPushButton("终止选中的进程")
        terminate_btn.clicked.connect(self.terminate_selected)

        main_layout.addWidget(launch_group)
        main_layout.addWidget(self.table)
        main_layout.addWidget(terminate_btn)

        # 定时更新后台进程状态
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_process_status)
        self.timer.start(1000)

    def browse_program(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "",
            "所有文件 (*.*);;可执行文件 (*.exe *.bat *.cmd);;Python脚本 (*.py)"
        )
        if file_path:
            self.program_path_edit.setText(file_path)

    def launch_process(self):
        program = self.program_path_edit.text().strip()
        if not program:
            QMessageBox.warning(self, "警告", "请选择要启动的程序")
            return

        # 处理 Python 脚本
        actual_program = program
        args = shlex.split(self.args_edit.text().strip()) if self.args_edit.text().strip() else []
        if program.lower().endswith('.py'):
            python_exe = shutil.which('python') or shutil.which('python3')
            if not python_exe:
                QMessageBox.critical(self, "错误", "未找到 Python 解释器，请确保 Python 已安装并添加到 PATH")
                return
            actual_program = python_exe
            args = [program] + args

        # 构建完整的命令字符串（用于显示）
        full_cmd = f"{actual_program} {' '.join(shlex.quote(a) for a in args)}" if args else actual_program

        if self.interactive_cb.isChecked():
            # ========== 交互模式：在新系统终端中运行 ==========
            terminal_pid = self._launch_in_terminal(actual_program, args, full_cmd)
            if terminal_pid is None:
                return

            row = self.table.rowCount()
            self.table.insertRow(row)
            name = program.split("/")[-1].split("\\")[-1]
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(terminal_pid)))
            self.table.setItem(row, 2, QTableWidgetItem("运行中(交互)"))
            self.table.setItem(row, 3, QTableWidgetItem(full_cmd))

            # 终止按钮
            btn_terminate = QPushButton("终止")
            btn_terminate.clicked.connect(lambda checked, r=row: self.terminate_process_by_row(r))
            self.table.setCellWidget(row, 4, btn_terminate)

            # 查看输出按钮（交互模式下不可用，因为终端已提供完整I/O）
            btn_output = QPushButton("终端已交互")
            btn_output.setEnabled(False)
            self.table.setCellWidget(row, 5, btn_output)

            # 存储交互模式进程（注意这里存储的是终端进程的PID）
            self.processes.append((terminal_pid, row, name, full_cmd, "interactive"))
            QMessageBox.information(self, "成功", f"已在独立终端中启动 {name} (终端PID: {terminal_pid})\n可直接在终端中输入交互。")
        else:
            # ========== 后台模式：原有逻辑 ==========
            self._launch_background(actual_program, args, full_cmd, program)

    def _launch_in_terminal(self, program, args, full_cmd):
        """在新终端中运行命令，返回终端进程的PID，失败返回None"""
        system = platform.system()
        try:
            if system == "Windows":
                # Windows: 使用 start 打开 cmd 并执行命令，窗口保持打开
                # 注意命令行需要正确转义
                cmd_line = f'start "Interactive Process" cmd /k "{program} {" ".join(args)}"'
                # 使用 CREATE_NEW_CONSOLE 标志创建新窗口，以便获取PID
                proc = subprocess.Popen(cmd_line, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                return proc.pid
            elif system == "Linux":
                # Linux: 尝试多种终端模拟器
                terminals = [
                    ("gnome-terminal", ["--", "bash", "-c", f"{program} {shlex.join(args)}; exec bash"]),
                    ("konsole", ["-e", "bash", "-c", f"{program} {shlex.join(args)}; exec bash"]),
                    ("xterm", ["-e", f"{program} {shlex.join(args)}"]),
                    ("lxterminal", ["-e", f"{program} {shlex.join(args)}"])
                ]
                for term, term_args in terminals:
                    if subprocess.call(["which", term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                        proc = subprocess.Popen([term] + term_args)
                        return proc.pid
                QMessageBox.warning(self, "警告", "未找到支持的终端模拟器 (gnome-terminal, konsole, xterm 等)")
                return None
            elif system == "Darwin":
                # macOS: 使用 Terminal.app
                script = f'tell application "Terminal" to do script "{program} {shlex.join(args)}"'
                proc = subprocess.Popen(["osascript", "-e", script])
                # osascript 返回的 PID 是 AppleScript 进程，不是终端进程，但终止时可以用它关闭终端
                return proc.pid
            else:
                QMessageBox.warning(self, "警告", f"不支持的操作系统: {system}")
                return None
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法启动终端: {str(e)}")
            return None

    def _launch_background(self, program, args, full_cmd, original_program):
        """后台模式：使用 QProcess 重定向输出到日志文件"""
        log_file = tempfile.NamedTemporaryFile(prefix="proc_log_", suffix=".txt", delete=False)
        log_file.close()
        log_path = log_file.name

        process = QProcess(self)
        process.setProgram(program)
        process.setArguments(args)
        process.setStandardOutputFile(log_path)
        process.setStandardErrorFile(log_path, QProcess.OpenModeFlag.Append)

        process.finished.connect(lambda ec, es, p=process: self.on_process_finished(p, ec, es))
        process.errorOccurred.connect(lambda err, p=process: self.on_process_error(p, err))

        process.start()
        if not process.waitForStarted(3000):
            QMessageBox.critical(self, "错误", f"无法启动进程: {program}\n错误: {process.errorString()}")
            return

        pid = process.processId()
        name = original_program.split("/")[-1].split("\\")[-1]

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(str(pid)))
        self.table.setItem(row, 2, QTableWidgetItem("运行中"))
        self.table.setItem(row, 3, QTableWidgetItem(full_cmd))

        btn_terminate = QPushButton("终止")
        btn_terminate.clicked.connect(lambda checked, r=row: self.terminate_process_by_row(r))
        self.table.setCellWidget(row, 4, btn_terminate)

        btn_output = QPushButton("终端查看")
        btn_output.clicked.connect(lambda checked, r=row: self.view_output_in_terminal(r))
        self.table.setCellWidget(row, 5, btn_output)

        self.processes.append((process, row, name, pid, full_cmd, log_path, "background"))
        self.args_edit.clear()
        QMessageBox.information(self, "成功", f"后台进程 {name} (PID: {pid}) 已启动\n日志文件: {log_path}")

    def view_output_in_terminal(self, row):
        """后台模式：在终端中 tail 日志文件"""
        for item in self.processes:
            if len(item) == 7 and item[1] == row and item[6] == "background":
                _, _, _, _, _, log_path, _ = item
                if not QFile(log_path).exists():
                    QMessageBox.warning(self, "警告", "日志文件不存在")
                    return
                system = platform.system()
                try:
                    if system == "Windows":
                        cmd = f'powershell -NoExit -Command "Get-Content -Path \\"{log_path}\\" -Wait"'
                        subprocess.Popen(f'start {cmd}', shell=True)
                    elif system == "Linux":
                        terminals = [("gnome-terminal", ["--", "bash", "-c", f"tail -f '{log_path}'; exec bash"]),
                                     ("xterm", ["-e", f"tail -f '{log_path}'"])]
                        for term, args in terminals:
                            if subprocess.call(["which", term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                                subprocess.Popen([term] + args)
                                break
                    elif system == "Darwin":
                        subprocess.Popen(["osascript", "-e", f'tell application "Terminal" to do script "tail -f \\"{log_path}\\""'])
                    else:
                        QMessageBox.warning(self, "警告", f"不支持的操作系统: {system}")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"无法打开终端: {str(e)}")
                return
        QMessageBox.warning(self, "错误", "未找到对应的日志文件")

    def terminate_process_by_row(self, row):
        for item in self.processes:
            if item[1] == row:
                if item[-1] == "background":  # 后台模式
                    process = item[0]
                    name = item[2]
                    pid = item[3]
                    self._terminate_qprocess(process, name, pid, row)
                elif item[-1] == "interactive":  # 交互模式
                    terminal_pid = item[0]
                    name = item[2]
                    self._terminate_terminal(terminal_pid, name, row)
                break

    def terminate_selected(self):
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先在表格中选择要终止的进程")
            return
        for row in selected_rows:
            self.terminate_process_by_row(row)

    def _terminate_qprocess(self, process, name, pid, row):
        if process.state() == QProcess.ProcessState.Running:
            process.terminate()
            if not process.waitForFinished(3000):
                process.kill()
            self.table.item(row, 2).setText("已终止")
            btn = self.table.cellWidget(row, 4)
            if btn:
                btn.setEnabled(False)
            QMessageBox.information(self, "终止", f"后台进程 {name} (PID: {pid}) 已终止")
        else:
            QMessageBox.warning(self, "警告", f"进程 {name} 不在运行状态")

    def _terminate_terminal(self, terminal_pid, name, row):
        """终止终端进程（将导致其子进程也结束）"""
        try:
            if platform.system() == "Windows":
                subprocess.run(f"taskkill /F /PID {terminal_pid}", shell=True, capture_output=True)
            else:
                os.kill(terminal_pid, 15)  # SIGTERM
                import time
                time.sleep(0.5)
                os.kill(terminal_pid, 9)   # 确保杀死
            self.table.item(row, 2).setText("已终止")
            btn = self.table.cellWidget(row, 4)
            if btn:
                btn.setEnabled(False)
            QMessageBox.information(self, "终止", f"交互终端 {name} (终端PID: {terminal_pid}) 已关闭")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法终止终端进程: {str(e)}")

    def on_process_finished(self, process, exit_code, exit_status):
        for item in self.processes:
            if len(item) == 7 and item[0] == process and item[6] == "background":
                row = item[1]
                self.table.item(row, 2).setText("已退出")
                btn = self.table.cellWidget(row, 4)
                if btn:
                    btn.setEnabled(False)
                break

    def on_process_error(self, process, error):
        for item in self.processes:
            if len(item) == 7 and item[0] == process and item[6] == "background":
                row = item[1]
                self.table.item(row, 2).setText(f"错误: {error}")
                break

    def update_process_status(self):
        # 仅更新后台进程的运行状态（QProcess 自己会更新状态）
        for item in self.processes:
            if len(item) == 7 and item[6] == "background":
                proc, row, name, pid, _, _, _ = item
                if proc.state() == QProcess.ProcessState.Running:
                    if self.table.item(row, 2).text() != "运行中":
                        self.table.item(row, 2).setText("运行中")
                elif proc.state() == QProcess.ProcessState.NotRunning:
                    current = self.table.item(row, 2).text()
                    if current not in ("已终止", "已退出", "错误"):
                        self.table.item(row, 2).setText("未运行")
        # 交互模式的状态由用户操作决定，不自动更新

    def closeEvent(self, event: QCloseEvent):
        # 清理后台模式的日志文件
        for item in self.processes:
            if len(item) == 7 and item[6] == "background":
                _, _, _, _, _, log_path, _ = item
                try:
                    if os.path.exists(log_path):
                        os.unlink(log_path)
                except Exception:
                    pass
        event.accept()


if __name__ == "__main__":
    import shutil, os
    app = QApplication(sys.argv)
    window = ProcessManager()
    window.show()
    sys.exit(app.exec())