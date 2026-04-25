import PyQt6
from PyQt6 import QtCore, QtGui, QtWidgets

class QuickQLineEdit(QtWidgets.QLineEdit):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, Display, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
        self.setPlaceholderText(Display)
        self.textChanged.connect(self.EmitOutput)
    def EmitOutput(self):
        self.GetOutput.emit({self.OutputKey: self.text()})

class QuickQComboBox(QtWidgets.QComboBox):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, Display, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
        self.addItem(Display)
        self.currentIndexChanged.connect(self.EmitOutput)
    def EmitOutput(self):
        self.GetOutput.emit({self.OutputKey: self.currentText()})

class QuickQSpinBox(QtWidgets.QSpinBox):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, Display, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
        self.setValue(Display)
        self.valueChanged.connect(self.EmitOutput)
    def EmitOutput(self):
        self.GetOutput.emit({self.OutputKey: self.value()})

class QuickQDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, Display, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
        self.setValue(Display)
        self.valueChanged.connect(self.EmitOutput)
    def EmitOutput(self):
        self.GetOutput.emit({self.OutputKey: self.value()})

class QuickQCheckBox(QtWidgets.QCheckBox):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, Display, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
        self.setText(Display)
        self.stateChanged.connect(self.EmitOutput)
    def EmitOutput(self):
        self.GetOutput.emit({self.OutputKey: self.isChecked()})

class QuickQTextEdit(QtWidgets.QTextEdit):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, Display, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
        self.setPlainText(Display)
        self.textChanged.connect(self.EmitOutput)
    def EmitOutput(self):
        self.GetOutput.emit({self.OutputKey: self.toPlainText()})

class QuickQPushButton(QtWidgets.QPushButton):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, Display, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
        self.setText(Display)
        self.clicked.connect(self.EmitOutput)
    def EmitOutput(self):
        self.GetOutput.emit({self.OutputKey: True})

class QuickQListWidget(QtWidgets.QListWidget):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
        self.itemSelectionChanged.connect(self.EmitOutput)
    def EmitOutput(self):
        selected_items = self.selectedItems()
        selected_texts = [item.text() for item in selected_items]
        self.GetOutput.emit({self.OutputKey: selected_texts})

class QuickQRadioButton(QtWidgets.QRadioButton):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, Display, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
        self.setText(Display)
        self.toggled.connect(self.EmitOutput)
    def EmitOutput(self):
        self.GetOutput.emit({self.OutputKey: self.isChecked()})

class QuickQWidget(QtWidgets.QWidget):
    GetOutput = QtCore.pyqtSignal(dict)
    def __init__(self, OutputKey, parent=None):
        super().__init__(parent)
        self.OutputKey = OutputKey
    def HandleOutput(self, DictInput):
        self.GetOutput.emit({self.OutputKey: DictInput})