import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from shell import CommandError, Shell
from vfs import VirtualFileSystem
class MutationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        (self.root / 'empty').mkdir()
        (self.root / 'a' / 'b').mkdir(parents=True)
        (self.root / 'docs').mkdir()
        (self.root / 'docs' / 'file').write_bytes(b'original')
        self.shell = Shell(VirtualFileSystem(self.root))
    def test_ownership_in_memory(self):
        before = (self.root / 'docs' / 'file').stat()
        self.shell.execute('chown -R user:team docs')
        self.assertEqual(self.shell.vfs.get('/docs/file')['owner'], 'user')
        self.assertEqual(self.shell.vfs.get('/docs/file')['group'], 'team')
        self.assertIn('user team', self.shell.execute('ls -l docs'))
        self.shell.execute('chown :other docs/file')
        self.assertEqual(self.shell.vfs.get('/docs/file')['owner'], 'user')
        self.assertEqual(self.shell.vfs.get('/docs/file')['group'], 'other')
        self.assertEqual((self.root / 'docs' / 'file').stat().st_uid, before.st_uid)
        self.assertEqual((self.root / 'docs' / 'file').stat().st_gid, before.st_gid)
        self.assertNotEqual(VirtualFileSystem(self.root).get('/docs/file')['owner'], 'user')
    def test_remove_empty_and_parents(self):
        self.shell.execute('rmdir empty')
        self.assertNotIn('/empty', self.shell.vfs.entries)
        self.assertTrue((self.root / 'empty').is_dir())
        self.shell.execute('rmdir -p a/b')
        self.assertNotIn('/a', self.shell.vfs.entries)
        self.assertTrue((self.root / 'a' / 'b').is_dir())
        self.assertEqual((self.root / 'docs' / 'file').read_bytes(), b'original')
    def test_mutation_errors(self):
        for line in ('chown', 'chown user', 'chown : docs', 'chown user: docs',
                     'chown user missing', 'rmdir', 'rmdir docs', 'rmdir docs/file',
                     'rmdir /', 'rmdir missing', 'rmdir -z empty'):
            with self.subTest(line=line):
                with self.assertRaises(CommandError):
                    self.shell.execute(line)
        self.shell.execute('cd empty')
        with self.assertRaises(CommandError):
            self.shell.execute('rmdir /empty')
