import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("可交互的嵌入图表")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建 matplotlib 图形
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # 生成数据
        self.x = np.linspace(0, 10, 100)
        self.y = np.sin(self.x)
        self.line, = self.ax.plot(self.x, self.y, picker=True, pickradius=5)

        # 绑定点击事件
        self.canvas.mpl_connect('pick_event', self.on_pick)

    def on_pick(self, event):
        # 点击曲线时的回调函数
        artist = event.artist
        if artist == self.line:
            # 获取点击点在曲线上的索引
            ind = event.ind[0]
            # 高亮显示点击的数据点
            self.ax.scatter(self.x[ind], self.y[ind], color='red', s=50)
            self.canvas.draw()
            print(f"点击了数据点: ({self.x[ind]:.2f}, {self.y[ind]:.2f})")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())