import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from config import CommandLog, read_config
from gui import ShellWindow
from shell import Shell
class ConfigTests(unittest.TestCase):
    def test_arguments(self):
        config = read_config(['--vfs', 'data', '--log', 'events.xml', '--script', 'start.txt'])
        self.assertEqual((config.vfs, config.log, config.script), ('data', 'events.xml', 'start.txt'))
    def test_script_and_xml(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            script = path / 'start.txt'
            script.write_text('unknown\nls\nexit\ncd docs', encoding='utf-8')
            window = ShellWindow(Shell(), logger=CommandLog(path / 'log.xml'))
            window.run_script(script)
            events = ET.parse(path / 'log.xml').getroot().findall('event')
            self.assertEqual([event.findtext('command') for event in events], ['unknown', 'ls', 'exit'])
            self.assertIn('Неизвестная команда', events[0].findtext('error'))
            self.assertTrue(events[0].findtext('datetime'))
            self.assertIn('hello.txt', window.output.toPlainText())
            self.assertTrue(window.shell.closed)
