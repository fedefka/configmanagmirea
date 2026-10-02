from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from shell import CommandError, VFS_NAME


class ShellWindow:

    def __init__(self, shell, vfs_name=VFS_NAME, logger=None):
        self.shell = shell
        self.vfs_name = vfs_name
        self.logger = logger
        self.app = QApplication.instance() or QApplication([])
        self.root = QWidget()
        self.root.setWindowTitle("Эмулятор - " + self.vfs_name)
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
        row.addWidget(QLabel(self.vfs_name + " $"))
        row.addWidget(self.entry, 1)
        row.addWidget(button)
        layout.addLayout(row)
        self.entry.setFocus()

    def write(self, text):
        if text:
            self.output.appendPlainText(text)

    def execute_line(self, line):
        self.write(self.vfs_name + " $ " + line)
        error_message = ""
        try:
            self.write(self.shell.execute(line))
        except CommandError as error:
            error_message = str(error)
            self.write("Ошибка: " + error_message)
        if self.logger and line.strip():
            try:
                self.logger.record(line, error_message)
            except OSError as error:
                self.write("Ошибка записи лога: " + str(error))
        if self.shell.closed:
            self.root.close()

    def submit(self):
        line = self.entry.text()
        self.entry.clear()
        self.execute_line(line)

    def run_script(self, path):
        from pathlib import Path
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            self.execute_line(line)
            if self.shell.closed:
                break

    def run(self):
        self.root.show()
        self.app.exec()
