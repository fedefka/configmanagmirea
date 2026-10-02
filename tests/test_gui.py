import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gui import ShellWindow
from shell import Shell


class WindowTests(unittest.TestCase):

    def test_dialogue(self):
        shell = Shell()
        window = ShellWindow(shell)
        window.root.show()
        window.app.processEvents()
        self.assertIn("VFS", window.root.windowTitle())
        self.assertEqual(window.output.toPlainText(), "")
        for line in ("ls", "cd /", "unknown", "cd a b"):
            window.entry.setText(line)
            window.entry.returnPressed.emit()
            window.app.processEvents()
        text = window.output.toPlainText()
        self.assertIn("hello.txt", text)
        self.assertIn("VFS $ cd /", text)
        self.assertIn("Неизвестная команда", text)
        self.assertIn("Ожидается не более одного пути", text)
        self.assertTrue(window.output.isReadOnly())
        window.entry.setText("exit")
        window.entry.returnPressed.emit()
        window.app.processEvents()
        self.assertTrue(shell.closed)
        self.assertFalse(window.root.isVisible())
