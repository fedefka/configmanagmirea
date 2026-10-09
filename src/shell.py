import os
import posixpath
import shlex
from pathlib import Path
from vfs import VFSError, VirtualFileSystem
VFS_NAME = 'VFS'
class CommandError(Exception):
    pass
def parse_command(line):
    try:
        arguments = shlex.split(line)
    except ValueError as error:
        raise CommandError('Неверные кавычки: ' + str(error)) from error
    return [os.path.expandvars(argument) for argument in arguments]
class Shell:
    def __init__(self, vfs=None):
        self.closed = False
        self.vfs = vfs or VirtualFileSystem(Path(__file__).resolve().parents[1] / 'examples/vfs/minimal')
        self.current = '/'
    def execute(self, line):
        parts = parse_command(line)
        if not parts:
            return ''
        command, arguments = parts[0], parts[1:]
        commands = {'ls': self.ls, 'cd': self.cd, 'wc': self.wc, 'tree': self.tree,
                    'exit': self.exit}
        if command not in commands:
            raise CommandError('Неизвестная команда: ' + command)
        try:
            return commands[command](arguments)
        except VFSError as error:
            raise CommandError(command + ': ' + str(error)) from error
    def exit(self, arguments):
        if arguments:
            raise CommandError('exit: аргументы не поддерживаются')
        self.closed = True
        return 'Завершение работы'
    def options(self, arguments, allowed):
        flags = set()
        paths = []
        options_enabled = True
        for argument in arguments:
            if options_enabled and argument == '--':
                options_enabled = False
            elif options_enabled and argument.startswith('-'):
                for flag in argument[1:]:
                    if flag not in allowed:
                        raise CommandError('Неизвестный параметр: -' + flag)
                    flags.add(flag)
                if argument == '-':
                    raise CommandError('Ожидается путь к файлу')
            else:
                paths.append(argument)
        return flags, paths
    def one_path(self, arguments, default):
        if len(arguments) > 1:
            raise CommandError('Ожидается не более одного пути')
        return self.vfs.resolve(arguments[0] if arguments else default, self.current)
    def ls(self, arguments):
        flags, paths = self.options(arguments, 'al')
        path = self.one_path(paths, self.current)
        entry = self.vfs.get(path)
        names = self.vfs.children(path) if entry['directory'] else [path]
        if 'a' not in flags:
            names = [name for name in names if not posixpath.basename(name).startswith('.')]
        lines = []
        for name in names:
            item = self.vfs.get(name)
            label = posixpath.basename(name)
            if 'l' in flags:
                label = '{} {} {} {}'.format('d' if item['directory'] else '-',
                                             item['owner'], len(item['data']), label)
            lines.append(label)
        return '\n'.join(lines)
    def cd(self, arguments):
        path = self.one_path(arguments, '/')
        if not self.vfs.get(path)['directory']:
            raise VFSError('Не является директорией: ' + path)
        self.current = path
        return ''
    def wc(self, arguments):
        flags, paths = self.options(arguments, 'lwmc')
        if not paths:
            raise CommandError('wc: требуется хотя бы один файл')
        selected = [flag for flag in 'lwmc' if flag in flags] if flags else list('lwc')
        totals = {flag: 0 for flag in 'lwmc'}
        lines = []
        for name in paths:
            entry = self.vfs.get(self.vfs.resolve(name, self.current))
            if entry['directory']:
                raise VFSError('Не является файлом: ' + name)
            data = entry['data']
            text = data.decode('utf-8', errors='replace')
            counts = {'l': data.count(b'\n'), 'w': len(text.split()),
                      'm': len(text), 'c': len(data)}
            for flag in totals:
                totals[flag] += counts[flag]
            lines.append(' '.join(str(counts[flag]) for flag in selected) + ' ' + name)
        if len(paths) > 1:
            lines.append(' '.join(str(totals[flag]) for flag in selected) + ' total')
        return '\n'.join(lines)
    def tree(self, arguments):
        flags = set()
        paths = []
        depth_limit = None
        index = 0
        options_enabled = True
        while index < len(arguments):
            argument = arguments[index]
            if options_enabled and argument == '--':
                options_enabled = False
            elif options_enabled and argument == '-L':
                index += 1
                if index >= len(arguments) or not arguments[index].isdigit() or int(arguments[index]) < 1:
                    raise CommandError('tree: -L требует положительное целое число')
                depth_limit = int(arguments[index])
            elif options_enabled and argument.startswith('-'):
                if argument not in ('-a', '-d', '-ad', '-da'):
                    raise CommandError('tree: неизвестный параметр ' + argument)
                flags.update(argument[1:])
            else:
                paths.append(argument)
            index += 1
        path = self.one_path(paths, self.current)
        self.vfs.children(path)
        lines = [path]
        counts = [0, 0]
        def visit(directory, prefix, depth):
            if depth_limit is not None and depth > depth_limit:
                return
            children = self.vfs.children(directory)
            children = [name for name in children
                        if ('a' in flags or not posixpath.basename(name).startswith('.'))
                        and ('d' not in flags or self.vfs.get(name)['directory'])]
            for index, name in enumerate(children):
                last = index == len(children) - 1
                item = self.vfs.get(name)
                lines.append(prefix + ('`-- ' if last else '|-- ') + posixpath.basename(name))
                counts[0 if item['directory'] else 1] += 1
                if item['directory']:
                    visit(name, prefix + ('    ' if last else '|   '), depth + 1)
        visit(path, '', 1)
        lines.append('{} directories, {} files'.format(*counts))
        return '\n'.join(lines)
