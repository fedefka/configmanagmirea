from pathlib import Path
import posixpath


class VFSError(Exception):
    pass


class VirtualFileSystem:

    def __init__(self, source):
        source = Path(source)
        if not source.exists():
            raise VFSError('VFS не найдена: ' + str(source))
        if not source.is_dir() or source.is_symlink():
            raise VFSError('VFS должна быть директорией')
        self.name = source.name or 'VFS'
        self.entries = {}
        try:
            self.add_entry('/', source)
            for path in sorted(source.rglob('*')):
                if path.is_symlink() or not (path.is_file() or path.is_dir()):
                    raise VFSError('Неподдерживаемый объект VFS: ' + str(path))
                name = '/' + path.relative_to(source).as_posix()
                self.add_entry(name, path)
        except OSError as error:
            raise VFSError('Ошибка чтения VFS: ' + str(error)) from error

    def add_entry(self, name, path):
        self.entries[name] = {
            'directory': path.is_dir(),
            'data': b'' if path.is_dir() else path.read_bytes(),
            'owner': str(getattr(path.stat(), 'st_uid', 0)),
        }

    def resolve(self, path, current='/'):
        if not path.startswith('/'):
            path = posixpath.join(current, path)
        return '/' + posixpath.normpath('/' + path.lstrip('/')).lstrip('/')

    def get(self, path):
        if path not in self.entries:
            raise VFSError('Путь не найден: ' + path)
        return self.entries[path]

    def children(self, path):
        entry = self.get(path)
        if not entry['directory']:
            raise VFSError('Не является директорией: ' + path)
        return sorted(name for name in self.entries
                      if name != '/' and posixpath.dirname(name) == path)
