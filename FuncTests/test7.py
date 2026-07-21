from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QLabel
from qfluentwidgets import FluentWindow, SearchLineEdit, NavigationItemPosition, PushButton
from qfluentwidgets import FluentIcon as FIF

class SearchDemoWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("qfluentwidgets 搜索框演示")

        # 创建搜索页面
        self.search_page = QWidget()
        self.search_page.setObjectName("search_page")
        self.addSubInterface(self.search_page, FIF.SEARCH, "全局搜索", position=NavigationItemPosition.TOP)

        # 初始化搜索页面的布局
        layout = QVBoxLayout(self.search_page)

        # --- 添加搜索框 ---
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索音乐、设置、文档...")
        layout.addWidget(self.search_edit)

        # --- 搜索结果区域 ---
        self.result_label = QLabel("等待输入...")
        layout.addWidget(self.result_label)

        # 也可以添加其他示例功能
        self.example_button = PushButton("示例按钮 (这里可放置其他功能)")
        layout.addWidget(self.example_button)

        layout.addStretch()  # 让上方内容顶置

        # --- 信号连接 ---
        # 实时搜索: 每当文本改变就触发 (可选)
        self.search_edit.textChanged.connect(self.on_text_changed)
        # 主动确认: 按下Enter或点击搜索按钮时触发
        self.search_edit.searchSignal.connect(self.on_search)
        # 清空信号
        self.search_edit.clearSignal.connect(self.on_clear)

    def on_search(self, text):
        """用户明确执行搜索"""
        self.result_label.setText(f"🔍 正在搜索: {text}")

    def on_text_changed(self, text):
        """实时搜索: 输入内容实时变化 (如使用 suggest 功能)"""
        # 生产环境中可加入防抖逻辑
        if not text:
            self.result_label.setText("清空搜索框")
        else:
            self.result_label.setText(f"✍️ 正在输入: {text}")

    def on_clear(self):
        """清空搜索"""
        self.result_label.setText("已清空，等待新输入...")

if __name__ == "__main__":
    app = QApplication([])
    w = SearchDemoWindow()
    w.show()
    app.exec()