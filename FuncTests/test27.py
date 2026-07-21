import sys
from PyQt6.QtWidgets import QApplication, QDialog, QLineEdit, QVBoxLayout, QPushButton

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.input_field = QLineEdit(self)
        self.input_field.setText("对话框文本")
        self.button = QPushButton("确定", self)
        self.button.clicked.connect(self.accept)  # 点击按钮接受并关闭

        layout = QVBoxLayout()
        layout.addWidget(self.input_field)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def get_data(self):
        """提供一个方法来获取数据"""
        return self.input_field.text()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    
    # 显示对话框并等待用户操作
    result = dialog.exec()
    
    if result == QDialog.DialogCode.Accepted:
        # 用户点击了确定，可以安全获取数据
        data = dialog.get_data()
        print(f"对话框关闭，获取数据: {data}")
    else:
        print("用户取消了操作")