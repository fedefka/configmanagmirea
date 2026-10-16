import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as element_tree
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from config import CommandLog, read_config
from gui import ShellWindow
from shell import Shell
class ConfigTests(unittest.TestCase):
    def test_arguments(self):
        config = read_config(
            ['--vfs', 'data', '--log', 'events.xml', '--script', 'start.txt'])
        self.assertEqual((config.vfs, config.log, config.script),
                         ('data', 'events.xml', 'start.txt'))
    def test_script_and_xml(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            script = path / 'start.txt'
            script.write_text('unknown\nls\nexit\ncd docs', encoding='utf-8')
            window = ShellWindow(Shell(), logger=CommandLog(path / 'log.xml'))
            window.run_script(script)
            events = element_tree.parse(
                path / 'log.xml').getroot().findall('event')
            self.assertEqual([event.findtext('command')
                             for event in events], ['unknown', 'ls', 'exit'])
            self.assertIn('Неизвестная команда', events[0].findtext('error'))
            self.assertTrue(events[0].findtext('datetime'))
            self.assertIn('ls: аргументы []', window.output.toPlainText())
            self.assertTrue(window.shell.closed)
    def test_defaults_from_other_directory(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            with patch('os.getcwd', return_value=folder):
                config = read_config([])
        project = Path(__file__).resolve().parents[1]
        self.assertEqual(Path(config.vfs), project / 'examples/vfs/minimal')
        self.assertEqual(Path(config.log), project / 'logs/commands.xml')
    def test_start_from_src(self):
        import subprocess
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / 'start.txt'
            log = Path(folder) / 'events.xml'
            script.write_text('ls\nexit\n', encoding='utf-8')
            command = [
                sys.executable, str(project / 'src/main.py'),
                '--script', str(script), '--log', str(log),
            ]
            result = subprocess.run(
                command, cwd=project / 'src', env=os.environ.copy(),
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            commands = [
                event.findtext('command')
                for event in element_tree.parse(log).getroot()
            ]
            self.assertEqual(commands, ['ls', 'exit'])
