import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from vfs import VFSError, VirtualFileSystem


class VFSTests(unittest.TestCase):

    def test_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            nested = root / 'a' / 'b' / 'c'
            nested.mkdir(parents=True)
            file = nested / 'data.txt'
            file.write_bytes(b'original')
            vfs = VirtualFileSystem(root)
            file.write_bytes(b'changed')
            self.assertEqual(vfs.get('/a/b/c/data.txt')['data'], b'original')
            self.assertEqual(vfs.children('/a/b'), ['/a/b/c'])
            self.assertEqual(vfs.resolve('../c', '/a/b'), '/a/c')
            self.assertEqual(vfs.resolve('../../..'), '/')

    def test_invalid_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            file = root / 'file'
            file.write_text('data')
            for source in (root / 'missing', file):
                with self.assertRaises(VFSError):
                    VirtualFileSystem(source)
            (root / 'link').symlink_to(file)
            with self.assertRaises(VFSError):
                VirtualFileSystem(root)
