import PyQt6
from PyQt6 import QtCore, QtGui, QtWidgets
import json

__INNER_VERSION__ = "Alpha_0.0.1_202604"

EXAMPLE_DICT = {
    "WinTitle": "Example Wizard",
    "Options": {
        "Option1": "Value1",
        "Option2": "Value2"
    },
    "Pages": [
        {
            "PageTitle": "Page 1",
            "PageContent": [
                {"Type": "QLabel", "Text": "This is the first page."},
                {"Type": "QLineEdit", "Text": "Enter something..."},
                {"Type": "QPushButton", "Text": "Click me!"}
            ]
        },
    ]
}

class BasicQuickWizard(QtWidgets.QWizard):
    def __init__(self, title, pages, parent=None):
        super().__init__(parent)
        self.OutputDict = {}
        self.Exited = False
        self.setWindowTitle(title)
        self.finished.connect(self.ExitWizard)
        for page in pages:
            if isinstance(page, QtWidgets.QWizardPage):
                self.addPage(page)
            else:
                self.page_ = QtWidgets.QWizardPage()
                self.layout_ = QtWidgets.QVBoxLayout()
                page.GetOutput.connect(self.EditOutputDict)
                self.layout_.addWidget(page)
                self.page_.setLayout(self.layout_)
                self.addPage(self.page_)
    def EditOutputDict(self, DictInput):
        for key, value in DictInput.items():
            self.OutputDict[key] = value
    def ExitWizard(self):
        self.Exited = True
        print(self.OutputDict)
        self.close()
class DictQuickWizard(BasicQuickWizard):
    def __init__(self, page_dict: dict, parent=None,
                 DeactiveOption: bool = False, UnuseOptions: list = []):
        super().__init__(title=page_dict.get("WinTitle", "Quick Wizard"), pages=[], parent=parent)
        self.pages = []
        self.page_dict = page_dict
        self.WinTitle = self.page_dict.get("WinTitle", "Quick Wizard")
        self.setWindowTitle(self.WinTitle)
        self.Options = self.page_dict.get("Options", {})
        self.Pages = self.page_dict.get("Pages", [])
        if not DeactiveOption:
            for option, value in self.Options.items():
                if option not in UnuseOptions:
                    try:
                        getattr(self, f"set{option}")(value)
                    except AttributeError:
                        getattr(self, f"{option}")(value)
        for i in range(len(self.Pages)):
            page = self.Pages[i]
            page_title = page.get("PageTitle", f"Page {i+1}")
            page_content = page.get("PageContent", [])
            page_widgets = []
            for widget in page_content:
                try:
                    widget_type = getattr(QtWidgets, widget.get("Type", "QLabel"))
                except AttributeError:
                    widget_type = QtWidgets.QLabel
                widget_text = widget.get("Text", "")
                widget_obj = widget_type(widget_text)
                page_widgets.append(widget_obj)
            page_layout = QtWidgets.QVBoxLayout()
            for widget in page_widgets:
                page_layout.addWidget(widget)
            wizard_page = QtWidgets.QWizardPage()
            wizard_page.setTitle(page_title)
            wizard_page.setSubTitle(f"Page {i+1} of {len(self.Pages)}")
            wizard_page.setLayout(page_layout)
            self.pages.append(wizard_page)
        super().__init__(self.WinTitle, self.pages, parent)

class JSONQuickWizard(DictQuickWizard):
    def __init__(self, json_str: str, parent=None,
                 DeactiveOption: bool = False, UnuseOptions: list = []):
        page_dict = json.loads(json_str)
        super().__init__(page_dict, parent, DeactiveOption, UnuseOptions)

class JSONFileQuickWizard(JSONQuickWizard):
    def __init__(self, json_file: str, parent=None,
                 DeactiveOption: bool = False, UnuseOptions: list = []):
        with open(json_file, 'r') as f:
            json_str = f.read()
        super().__init__(json_str, parent, DeactiveOption, UnuseOptions)

class BasicQuickWizardWithDefaultWelcomePage(BasicQuickWizard):
    def __init__(self, title, pages,hint=None, parent=None):
        welcome_page = QtWidgets.QWizardPage()
        welcome_layout = QtWidgets.QVBoxLayout()
        welcome_label = QtWidgets.QLabel(f"欢迎使用快速向导！\n\n{hint}\n\n请点击下一步继续。\n\n\n\n\n\n")
        Version = QtWidgets.QLabel(f"当前版本: {__INNER_VERSION__}")
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addWidget(Version)
        welcome_page.setLayout(welcome_layout)
        super().__init__(title, [welcome_page] + pages, parent)
        self.setPixmap(QtWidgets.QWizard.WizardPixmap.WatermarkPixmap, QtGui.QPixmap(":/icon/icon.png"))

if __name__ == "__main__":
    import sys
    import QuickQobjForQuickWizard 
    app = QtWidgets.QApplication(sys.argv)
    label = QuickQobjForQuickWizard.QuickQLineEdit("This is a quick wizard page.", "ExampleInput")
    wizard = BasicQuickWizardWithDefaultWelcomePage("Example Wizard", [label], hint="这是一个示例向导。")
    wizard.exec()