import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from qtreload import QtReloadWidget  # 导入 QtReloadWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 1. 实例化热重载组件，传入需要监控的模块名列表
        #    例如，如果你的主模块是 __main__，或者有自定义模块 "my_widgets"
        reload_widget = QtReloadWidget(["Entry_Main"])  # [reference:4]

        # 2. 将热重载组件添加到主窗口布局中
        #    注意：必须保持对 reload_widget 的引用，防止被垃圾回收[reference:5]
        layout.addWidget(reload_widget)

        # ... 你的其他 UI 代码 ...

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())