import sys
import numpy as np
from PyQt6.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt
import pyqtgraph as pg

class CurveEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('可拖拽曲线编辑器')
        self.setGeometry(100, 100, 800, 600)

        # 中心部件：绘图区
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # PyQtGraph 绘图区域
        self.plot = pg.PlotWidget()
        self.plot.setLabel('left', 'Y值')
        self.plot.setLabel('bottom', 'X值')
        self.plot.showGrid(x=True, y=True, alpha=0.5)
        layout.addWidget(self.plot)

        # 控制按钮
        self.add_btn = QPushButton('添加数据点')
        self.add_btn.clicked.connect(self.add_point)
        layout.addWidget(self.add_btn)

        # 初始化数据
        self.x = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.y = np.array([2, 1.5, 2.5, 3, 2.8, 3.2, 3.5, 3, 2.5, 2])
        self.dragged_point_idx = None

        # 绘制曲线
        self.curve = self.plot.plot(self.x, self.y, pen=pg.mkPen('b', width=2))
        self.points = pg.ScatterPlotItem(self.x, self.y, size=12, 
                                          pen=pg.mkPen('r'), brush=pg.mkBrush('r'))
        self.plot.addItem(self.points)

        # 启用鼠标跟踪
        self.plot.setMouseTracking(True)
        self.plot.scene().sigMouseMoved.connect(self.on_mouse_moved)
        # 重写鼠标事件（需要在 ViewBox 上处理）
        self.plot.vb.mousePressEvent = self.vb_press_event
        self.plot.vb.mouseMoveEvent = self.vb_move_event
        self.plot.vb.mouseReleaseEvent = self.vb_release_event

    def find_point_at(self, x, y, threshold=15):
        """查找距离点击位置最近的数据点"""
        min_dist = float('inf')
        nearest_idx = None
        for i, (px, py) in enumerate(zip(self.x, self.y)):
            dx = abs(px - x)
            dy = abs(py - y)
            if dx < threshold and dy < threshold:
                dist = dx**2 + dy**2
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = i
        return nearest_idx

    def update_curve(self):
        """更新曲线和散点数据"""
        self.curve.setData(self.x, self.y)
        self.points.setData(self.x, self.y)
        # 如果启用了 smooth_curve，在此处重新计算样条

    def add_point(self):
        """在末尾添加新数据点"""
        new_x = len(self.x)
        new_y = self.y[-1] - 0.5 if self.y[-1] > 0 else self.y[-1] + 0.5
        self.x = np.append(self.x, new_x)
        self.y = np.append(self.y, new_y)
        self.update_curve()

    def vb_press_event(self, ev):
        """鼠标按下"""
        if ev.button() == Qt.MouseButton.LeftButton:
            pos = self.plot.vb.mapSceneToView(ev.scenePos())
            self.dragged_point_idx = self.find_point_at(pos.x(), pos.y())
        # 调用原始事件处理
        pg.ViewBox.mousePressEvent(self.plot.vb, ev)

    def vb_move_event(self, ev):
        """鼠标移动"""
        if self.dragged_point_idx is not None and ev.buttons() == Qt.MouseButton.LeftButton:
            pos = self.plot.vb.mapSceneToView(ev.scenePos())
            self.y[self.dragged_point_idx] = pos.y()
            self.update_curve()
        pg.ViewBox.mouseMoveEvent(self.plot.vb, ev)

    def vb_release_event(self, ev):
        """鼠标释放"""
        self.dragged_point_idx = None
        pg.ViewBox.mouseReleaseEvent(self.plot.vb, ev)

    def on_mouse_moved(self, pos):
        """显示鼠标实时坐标"""
        if self.plot.sceneBoundingRect().contains(pos):
            mouse_point = self.plot.vb.mapSceneToView(pos)
            self.setWindowTitle(f"坐标: ({mouse_point.x():.2f}, {mouse_point.y():.2f})")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CurveEditor()
    window.show()
    sys.exit(app.exec())