from qfluentwidgets import FluentWindow, NavigationItemPosition
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtWidgets import QApplication

class MyWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        
        # 创建页面
        self.home_page = QWidget()
        self.settings_page = QWidget()

        self.home_page.setObjectName('homeInterface')
        self.settings_page.setObjectName('settingsInterface')

        # 添加导航项
        self.addSubInterface(self.home_page, 'homeInterface', '首页')
        self.addSubInterface(self.settings_page, 'settingsInterface', '设置',
                             NavigationItemPosition.BOTTOM)  # 放在底部

# 运行窗口
if __name__ == "__main__":
    app = QApplication([])
    w = MyWindow()
    w.show()
    app.exec()