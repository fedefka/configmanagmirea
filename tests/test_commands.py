import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from shell import CommandError, Shell
from vfs import VirtualFileSystem


class CommandTests(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / 'a' / 'b' / 'c').mkdir(parents=True)
        (self.root / 'a' / 'b' / 'c' / 'data').write_text('А Б\n', encoding='utf-8')
        (self.root / 'text').write_text('one two\nlast', encoding='utf-8')
        (self.root / '.hidden').write_text('x')
        self.shell = Shell(VirtualFileSystem(self.root))

    def test_navigation_and_listing(self):
        self.assertEqual(self.shell.execute('ls'), 'a\ntext')
        self.assertIn('.hidden', self.shell.execute('ls -a'))
        self.shell.execute('cd a/b')
        self.assertEqual(self.shell.execute('ls'), 'c')
        self.shell.execute('cd ..')
        self.assertEqual(self.shell.current, '/a')
        self.shell.execute('cd')
        self.assertEqual(self.shell.current, '/')
        self.assertTrue(self.shell.execute('ls -l text').endswith(' 12 text'))
        for line in ('cd text', 'ls missing', 'ls -z', 'cd x y'):
            with self.assertRaises(CommandError):
                self.shell.execute(line)
        self.assertEqual(self.shell.current, '/')

    def test_wc_unicode_and_totals(self):
        self.assertEqual(self.shell.execute('wc text'), '1 3 12 text')
        self.assertEqual(self.shell.execute('wc -lwmc a/b/c/data'), '1 2 4 6 a/b/c/data')
        self.assertTrue(self.shell.execute('wc -c text a/b/c/data').endswith('18 total'))
        for line in ('wc', 'wc /', 'wc missing', 'wc -z text'):
            with self.assertRaises(CommandError):
                self.shell.execute(line)

    def test_tree_depth_and_directories(self):
        self.assertIn('data', self.shell.execute('tree'))
        self.assertNotIn('data', self.shell.execute('tree -L 2'))
        self.assertNotIn('text', self.shell.execute('tree -d'))
        self.assertIn('.hidden', self.shell.execute('tree -a'))
        for line in ('tree text', 'tree -L 0', 'tree -L', 'tree x y'):
            with self.assertRaises(CommandError):
                self.shell.execute(line)
