import sys
from PySide6.QtWidgets import QApplication
from .ui.main_window import App


def main():
    application = QApplication(sys.argv)
    application.setApplicationName("季节笔记")
    window = App()
    window.show()
    return application.exec()
