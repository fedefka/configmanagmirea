import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shell import CommandError, Shell, parse_command


class ShellTests(unittest.TestCase):

    def test_stubs(self):
        shell = Shell()
        self.assertEqual(shell.execute("ls"), "ls: аргументы []")
        self.assertEqual(shell.execute("cd docs"),
                         "cd: аргументы ['docs']")

    def test_environment_variables(self):
        with patch.dict(os.environ, {"SHELL_TEST": "/folder with spaces"}):
            for line in ('cd "$SHELL_TEST"', 'cd "${SHELL_TEST}"'):
                self.assertEqual(parse_command(line),
                                 ["cd", "/folder with spaces"])

    def test_empty_input_and_quoted_path(self):
        self.assertEqual(Shell().execute("   "), "")
        self.assertEqual(parse_command('cd "my docs"'), ["cd", "my docs"])

    def test_errors(self):
        for line in ("unknown", "cd a b", "ls a b", "exit now", 'cd "'):
            with self.subTest(line=line):
                with self.assertRaises(CommandError):
                    Shell().execute(line)

    def test_exit(self):
        shell = Shell()
        with self.assertRaises(CommandError):
            shell.execute("exit now")
        self.assertFalse(shell.closed)
        shell.execute("exit")
        self.assertTrue(shell.closed)
