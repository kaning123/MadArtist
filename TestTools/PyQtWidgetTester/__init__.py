import sys
import asyncio
import importlib
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout
from PyQt6.QtWidgets import QPushButton, QHBoxLayout
import qasync
from watchfiles import awatch
import importlib.util
import os
import time
import traceback
import argparse

def import_module_from_path(module_name, file_path):
    """
    从任意文件路径导入模块
    :param module_name: 模块名称（任意合法标识符）
    :param file_path: 模块文件的绝对路径
    :return: 导入的模块对象
    """
    # 1. 创建规格
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"无法从 {file_path} 创建模块规格")

    # 2. 创建模块对象
    module = importlib.util.module_from_spec(spec)

    # 3. 将模块添加到 sys.modules（可选，但推荐，以便后续导入或重载）
    sys.modules[module_name] = module

    # 4. 执行模块代码
    spec.loader.exec_module(module) # type: ignore

    return module



# ----------------------------------

class MainWindow(QMainWindow):
    def __init__(self, module):
        super().__init__()
        self.module = module          # 保存模块引用，以便重载
        self.current_widget = None
        self.setWindowTitle("Widget Hot Reloader")
        self.setGeometry(100, 100, 400, 300)
        self.hbox = QHBoxLayout()
        self.setLayout(self.hbox)
        self.load_widget()

    def load_widget(self):
        """首次或重载后加载新的 Widget"""
        self.hbox = QHBoxLayout()
        self.setLayout(self.hbox)
        widget = self.module.Main()   # 假设模块中有 Main 类
        self.setCentralWidget(widget)
        self.current_widget = widget

    def replace_widget(self):
        """安全替换中央 Widget（在重载后调用）"""
        if self.current_widget:
            self.current_widget.deleteLater()  # 删除旧的
        new_widget = self.module.Main()
        self.setCentralWidget(new_widget)
        self.current_widget = new_widget
        self.repaint()   # 强制刷新

async def watch_files(main_window, target):
    """异步监控文件变化，重载模块并刷新界面"""
    async for changes in awatch(target):
        for change_type, path in changes:
            print(f"检测到变化: {change_type} - {path}")
            try:
                # 1. 使导入缓存失效
                importlib.invalidate_caches()
                # 2. 重新加载模块（注意模块名必须与导入时一致）
                module_name = "Entry_Main"   # 与 import Entry_Main 对应
                if module_name in sys.modules:
                    main_window.module = importlib.reload(sys.modules[module_name])
                    # 3. 更新 UI（此协程运行在主线程，可直接操作 Qt）
                    main_window.replace_widget()
                    print("重载成功！")
                else:
                    print("模块未导入，无法重载")
            except Exception as e:
                print(f"重载失败: {e}")

async def main(load_path):
    # 创建 QApplication（如果尚未创建）
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 首次导入目标模块
    Entry_Main = import_module_from_path(os.path.basename(load_path), load_path)  # 导入后，模块会被加入 sys.modules
    window = MainWindow(Entry_Main)
    window.show()

    # 启动后台监控任务（不等待）
    asyncio.create_task(watch_files(window, os.path.dirname(load_path)))

    # 保持事件循环永久运行（等待一个永不触发的 Event）
    await asyncio.Event().wait()

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="MadArtist Widget Hot Reloader - Version Alpha_0.0.1_20260625")
    parser.add_argument("--load-path",
                        "-l",
                        required = True, 
                        type=str, 
                        help="目标模块的路径")
    args = parser.parse_args()
    # 使用 qasync.run() 统一管理事件循环
    # 它会自动启动 Qt 事件循环，并融合 asyncio
    qasync.run(main(args.load_path))