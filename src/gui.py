from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget,
)
from shell import CommandError, VFS_NAME
class ShellWindow:
    def __init__(self, shell):
        self.shell = shell
        self.app = QApplication.instance() or QApplication([])
        self.root = QWidget()
        self.root.setWindowTitle("Эмулятор - " + VFS_NAME)
        self.root.resize(760, 480)
        self.root.setMinimumSize(500, 300)
        layout = QVBoxLayout(self.root)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Menlo", 12))
        layout.addWidget(self.output)
        self.entry = QLineEdit()
        self.entry.setFont(QFont("Menlo", 12))
        self.entry.returnPressed.connect(self.submit)
        button = QPushButton("Выполнить")
        button.clicked.connect(self.submit)
        row = QHBoxLayout()
        row.addWidget(QLabel(VFS_NAME + " $"))
        row.addWidget(self.entry, 1)
        row.addWidget(button)
        layout.addLayout(row)
        self.entry.setFocus()
    def write(self, text):
        if text:
            self.output.appendPlainText(text)
    def submit(self):
        line = self.entry.text()
        self.entry.clear()
        self.write(VFS_NAME + " $ " + line)
        try:
            self.write(self.shell.execute(line))
        except CommandError as error:
            self.write("Ошибка: " + str(error))
        if self.shell.closed:
            self.root.close()
    def run(self):
        self.root.show()
        self.app.exec()
