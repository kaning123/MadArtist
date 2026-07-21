import sys
import platform
import subprocess
import tempfile
import shlex   # 仅保留 shlex.split 用于解析参数字符串
import shutil
import os
import time
import psutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QLineEdit, QLabel, QMessageBox, QHeaderView, QCheckBox, QInputDialog
)
from PyQt6.QtCore import QProcess, Qt, QTimer, QFile
from PyQt6.QtGui import QCloseEvent


class ProcessManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("进程管理器 - 支持终端交互与任意进程终止")
        self.setMinimumSize(950, 550)

        self.processes = []

        # 创建界面
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

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

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["进程名称", "PID", "状态", "启动命令", "终止", "终端输出"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        button_layout = QHBoxLayout()
        terminate_btn = QPushButton("终止选中的进程（本程序管理）")
        terminate_btn.clicked.connect(self.terminate_selected)
        kill_arbitrary_btn = QPushButton("结束任意进程（输入PID）")
        kill_arbitrary_btn.clicked.connect(self.kill_arbitrary_process)

        button_layout.addWidget(terminate_btn)
        button_layout.addWidget(kill_arbitrary_btn)

        main_layout.addWidget(launch_group)
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_process_status)
        self.timer.start(1000)

    # ---------- 辅助函数：安全地将参数列表拼接成命令行字符串（弃用 shlex.join） ----------
    @staticmethod
    def _quote_arg(arg: str) -> str:
        """如果参数包含空格或特殊字符，用双引号包裹（Windows 风格）"""
        # 简单处理：如果参数中包含空格，则用双引号包裹
        if ' ' in arg or '\t' in arg:
            return f'"{arg}"'
        return arg

    @staticmethod
    def _join_args(args_list):
        """将参数列表用空格连接，并对含有空格的参数自动添加双引号"""
        return ' '.join(ProcessManager._quote_arg(a) for a in args_list)

    # ---------- 原有方法（修改了命令构造部分） ----------
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

        actual_program = program
        raw_args = self.args_edit.text().strip()
        args = shlex.split(raw_args) if raw_args else []

        if program.lower().endswith('.py'):
            python_exe = shutil.which('python') or shutil.which('python3')
            if not python_exe:
                QMessageBox.critical(self, "错误", "未找到 Python 解释器，请确保 Python 已安装并添加到 PATH")
                return
            actual_program = python_exe
            args = [program] + args

        # 构建用于显示的完整命令（使用自定义拼接，不再依赖 shlex.join）
        if args:
            full_cmd = f"{actual_program} {self._join_args(args)}"
        else:
            full_cmd = actual_program

        if self.interactive_cb.isChecked():
            terminal_pid, real_pid = self._launch_in_terminal(actual_program, args, full_cmd)
            if terminal_pid is None:
                return

            row = self.table.rowCount()
            self.table.insertRow(row)
            name = program.split("/")[-1].split("\\")[-1]
            if real_pid:
                pid_display = str(real_pid)
                status_text = "运行中(交互)"
            else:
                pid_display = f"{terminal_pid} (终端)"
                status_text = "运行中(交互, 未找到子进程PID)"
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(pid_display))
            self.table.setItem(row, 2, QTableWidgetItem(status_text))
            self.table.setItem(row, 3, QTableWidgetItem(full_cmd))

            btn_terminate = QPushButton("终止")
            btn_terminate.clicked.connect(lambda checked, r=row: self.terminate_process_by_row(r))
            self.table.setCellWidget(row, 4, btn_terminate)

            btn_output = QPushButton("终端已交互")
            btn_output.setEnabled(False)
            self.table.setCellWidget(row, 5, btn_output)

            self.processes.append((terminal_pid, row, name, real_pid if real_pid else terminal_pid, full_cmd, "interactive"))
            msg = f"已在独立终端中启动 {name}\n终端 PID: {terminal_pid}"
            if real_pid:
                msg += f"\n目标程序 PID: {real_pid}"
            else:
                msg += "\n无法自动获取目标程序 PID，表格中显示的是终端 PID。"
            QMessageBox.information(self, "成功", msg)
        else:
            self._launch_background(actual_program, args, full_cmd, program)

    def _launch_in_terminal(self, program, args, full_cmd):
        system = platform.system()
        terminal_pid = None
        try:
            if system == "Windows":
                # 使用自定义的 _join_args 拼接参数
                args_part = self._join_args(args)
                cmd_line = f'start "Interactive Process" cmd /k "{program} {args_part}"'
                proc = subprocess.Popen(cmd_line, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                terminal_pid = proc.pid
                time.sleep(0.5)
                real_pid = self._find_real_pid_windows(terminal_pid, program)
                return terminal_pid, real_pid
            elif system == "Linux":
                terminals = [
                    ("gnome-terminal", ["--", "bash", "-c", f"{program} {self._join_args(args)}; exec bash"]),
                    ("konsole", ["-e", "bash", "-c", f"{program} {self._join_args(args)}; exec bash"]),
                    ("xterm", ["-e", f"{program} {self._join_args(args)}"]),
                    ("lxterminal", ["-e", f"{program} {self._join_args(args)}"])
                ]
                for term, term_args in terminals:
                    if subprocess.call(["which", term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                        proc = subprocess.Popen([term] + term_args)
                        terminal_pid = proc.pid
                        time.sleep(0.5)
                        real_pid = self._find_real_pid_unix(terminal_pid, program)
                        return terminal_pid, real_pid
                QMessageBox.warning(self, "警告", "未找到支持的终端模拟器 (gnome-terminal, konsole, xterm 等)")
                return None, None
            elif system == "Darwin":
                script = f'tell application "Terminal" to do script "{program} {self._join_args(args)}"'
                proc = subprocess.Popen(["osascript", "-e", script])
                terminal_pid = proc.pid
                time.sleep(0.5)
                real_pid = self._find_real_pid_unix(terminal_pid, program)
                return terminal_pid, real_pid
            else:
                QMessageBox.warning(self, "警告", f"不支持的操作系统: {system}")
                return None, None
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法启动终端: {str(e)}")
            return None, None

    def _find_real_pid_windows(self, terminal_pid, target_program):
        try:
            parent = psutil.Process(terminal_pid)
            children = parent.children(recursive=True)
            target_name = os.path.basename(target_program).lower()
            for child in children:
                try:
                    if child.name().lower() == target_name:
                        return child.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return None
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def _find_real_pid_unix(self, terminal_pid, target_program):
        try:
            parent = psutil.Process(terminal_pid)
            children = parent.children(recursive=True)
            target_name = os.path.basename(target_program)
            for child in children:
                try:
                    if child.name() == target_name or target_name in ' '.join(child.cmdline()):
                        return child.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return None
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    def _launch_background(self, program, args, full_cmd, original_program):
        log_file = tempfile.NamedTemporaryFile(prefix="proc_log_", suffix=".txt", delete=False)
        log_file.close()
        log_path = log_file.name

        process = QProcess(self)
        process.setProgram(program)
        process.setArguments(args)   # QProcess 直接使用参数列表，无需手动拼接
        process.setStandardOutputFile(log_path)
        process.setStandardErrorFile(log_path, QProcess.OpenModeFlag.Append)

        process.finished.connect(lambda ec, es, p=process: self.on_process_finished(p, ec, es))
        process.errorOccurred.connect(lambda err, p=process: self.on_process_error(p, err))

        process.start()
        if not process.waitForStarted(3000):
            QMessageBox.critical(self, "错误", f"无法启动进程: {program}\n错误: {process.errorString()}")
            return

        real_pid = None
        try:
            time.sleep(0.2)
            qpid = process.processId()
            if qpid:
                p = psutil.Process(qpid)
                real_pid = p.pid
        except Exception:
            real_pid = None
        if real_pid is None:
            real_pid = process.processId()

        name = original_program.split("/")[-1].split("\\")[-1]
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(str(real_pid)))
        self.table.setItem(row, 2, QTableWidgetItem("运行中"))
        self.table.setItem(row, 3, QTableWidgetItem(full_cmd))

        btn_terminate = QPushButton("终止")
        btn_terminate.clicked.connect(lambda checked, r=row: self.terminate_process_by_row(r))
        self.table.setCellWidget(row, 4, btn_terminate)

        btn_output = QPushButton("终端查看")
        btn_output.clicked.connect(lambda checked, r=row: self.view_output_in_terminal(r))
        self.table.setCellWidget(row, 5, btn_output)

        self.processes.append((process, row, name, real_pid, full_cmd, log_path, "background"))
        self.args_edit.clear()
        QMessageBox.information(self, "成功", f"后台进程 {name} (PID: {real_pid}) 已启动\n日志文件: {log_path}")

    # ---------- 其余方法（未修改，保持原样） ----------
    def view_output_in_terminal(self, row):
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
                        terminals = [
                            ("gnome-terminal", ["--", "bash", "-c", f"tail -f '{log_path}'; exec bash"]),
                            ("xterm", ["-e", f"tail -f '{log_path}'"])
                        ]
                        for term, term_args in terminals:
                            if subprocess.call(["which", term], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                                subprocess.Popen([term] + term_args)
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
                if item[-1] == "background":
                    process = item[0]
                    name = item[2]
                    pid = item[3]
                    self._terminate_qprocess(process, name, pid, row)
                elif item[-1] == "interactive":
                    terminal_pid = item[0]
                    real_pid = item[3]
                    name = item[2]
                    self._terminate_terminal(terminal_pid, real_pid, name, row)
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

    def _terminate_terminal(self, terminal_pid, real_pid, name, row):
        try:
            if platform.system() == "Windows":
                subprocess.run(f"taskkill /F /PID {terminal_pid}", shell=True, capture_output=True)
            else:
                os.kill(terminal_pid, 15)
                time.sleep(0.5)
                os.kill(terminal_pid, 9)
            self.table.item(row, 2).setText("已终止")
            btn = self.table.cellWidget(row, 4)
            if btn:
                btn.setEnabled(False)
            QMessageBox.information(self, "终止", f"交互终端 {name} (终端PID: {terminal_pid}, 程序PID: {real_pid}) 已关闭")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法终止终端进程: {str(e)}")

    def kill_arbitrary_process(self):
        pid_str, ok = QInputDialog.getText(self, "结束任意进程", "请输入要结束的进程 PID：")
        if not ok or not pid_str.isdigit():
            return
        pid = int(pid_str)
        try:
            proc = psutil.Process(pid)
            pname = proc.name()
        except psutil.NoSuchProcess:
            QMessageBox.warning(self, "错误", f"PID {pid} 对应的进程不存在")
            return
        self.kill_process(pid, pname)

    def kill_process(self, pid, pname):
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

    def closeEvent(self, event: QCloseEvent):
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
    app = QApplication(sys.argv)
    window = ProcessManager()
    window.show()
    sys.exit(app.exec())