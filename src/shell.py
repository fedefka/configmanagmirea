import os
import posixpath
import shlex
import re
from pathlib import Path
from vfs import VFSError, VirtualFileSystem
VFS_NAME = 'VFS'
CHOWN_MIN_ARGUMENTS = 2
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
        source = Path(__file__).resolve().parents[1] / 'examples/vfs/minimal'
        self.vfs = vfs or VirtualFileSystem(source)
        self.current = '/'
    def execute(self, line):
        parts = parse_command(line)
        if not parts:
            return ''
        command, arguments = parts[0], parts[1:]
        commands = {
            'ls': self.ls,
            'cd': self.cd,
            'wc': self.wc,
            'tree': self.tree,
            'exit': self.exit,
            'chown': self.chown,
            'rmdir': self.rmdir}
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
        value = arguments[0] if arguments else default
        return self.vfs.resolve(value, self.current)
    def ls(self, arguments):
        flags, paths = self.options(arguments, 'al')
        path = self.one_path(paths, self.current)
        entry = self.vfs.get(path)
        names = self.vfs.children(path) if entry['directory'] else [path]
        if 'a' not in flags:
            names = [name for name in names
                     if not posixpath.basename(name).startswith('.')]
        lines = []
        for name in names:
            item = self.vfs.get(name)
            label = posixpath.basename(name)
            if 'l' in flags:
                kind = 'd' if item['directory'] else '-'
                label = '{} {} {} {} {}'.format(
                    kind, item['owner'], item['group'], len(
                        item['data']), label)
            lines.append(label)
        return '\n'.join(lines)
    def cd(self, arguments):
        path = self.one_path(arguments, '/')
        if not self.vfs.get(path)['directory']:
            raise VFSError('Не является директорией: ' + path)
        self.current = path
        return ''
    def wc_counts(self, name):
        entry = self.vfs.get(self.vfs.resolve(name, self.current))
        if entry['directory']:
            raise VFSError('Не является файлом: ' + name)
        data = entry['data']
        text = data.decode('utf-8', errors='replace')
        return {'l': data.count(b'\n'), 'w': len(text.split()),
                'm': len(text), 'c': len(data)}
    def wc_line(self, counts, selected, name):
        values = ' '.join(str(counts[flag]) for flag in selected)
        return values + ' ' + name
    def wc(self, arguments):
        flags, paths = self.options(arguments, 'lwmc')
        if not paths:
            raise CommandError('wc: требуется хотя бы один файл')
        selected = list('lwc')
        if flags:
            selected = [flag for flag in 'lwmc' if flag in flags]
        totals = {flag: 0 for flag in 'lwmc'}
        lines = []
        for name in paths:
            counts = self.wc_counts(name)
            for flag in totals:
                totals[flag] += counts[flag]
            lines.append(self.wc_line(counts, selected, name))
        if len(paths) > 1:
            lines.append(self.wc_line(totals, selected, 'total'))
        return '\n'.join(lines)
    def tree_depth(self, arguments):
        if arguments:
            value = arguments.pop(0)
            if value.isdigit() and int(value) > 0:
                return int(value)
        raise CommandError('tree: -L требует положительное целое число')
    def tree_options(self, arguments):
        flags = set()
        paths = []
        depth_limit = None
        values = list(arguments)
        options_enabled = True
        while values:
            argument = values.pop(0)
            if options_enabled and argument == '--':
                options_enabled = False
            elif options_enabled and argument == '-L':
                depth_limit = self.tree_depth(values)
            elif options_enabled and argument.startswith('-'):
                if argument not in ('-a', '-d', '-ad', '-da'):
                    raise CommandError('tree: неизвестный параметр ' + argument)
                flags.update(argument[1:])
            else:
                paths.append(argument)
        return flags, paths, depth_limit
    def tree_children(self, directory, flags):
        children = self.vfs.children(directory)
        if 'a' not in flags:
            children = [name for name in children
                        if not posixpath.basename(name).startswith('.')]
        if 'd' in flags:
            children = [name for name in children
                        if self.vfs.get(name)['directory']]
        return children
    def tree_visit(self, directory, prefix, depth, state):
        flags, depth_limit, lines, counts = state
        if depth_limit is not None and depth > depth_limit:
            return
        children = self.tree_children(directory, flags)
        for index, name in enumerate(children):
            last = index == len(children) - 1
            item = self.vfs.get(name)
            connector = '`-- ' if last else '|-- '
            lines.append(prefix + connector + posixpath.basename(name))
            counts[0 if item['directory'] else 1] += 1
            if item['directory']:
                padding = '    ' if last else '|   '
                self.tree_visit(name, prefix + padding, depth + 1, state)
    def tree(self, arguments):
        flags, paths, depth_limit = self.tree_options(arguments)
        path = self.one_path(paths, self.current)
        self.vfs.children(path)
        lines = [path]
        counts = [0, 0]
        self.tree_visit(path, '', 1, (flags, depth_limit, lines, counts))
        lines.append('{} directories, {} files'.format(*counts))
        return '\n'.join(lines)
    def owner_values(self, value):
        owner, separator, group = value.partition(':')
        if not owner and not group:
            raise CommandError('chown: владелец или группа не заданы')
        for name in (owner, group):
            if name and not re.fullmatch(r'[A-Za-z0-9_.-]+', name):
                raise CommandError('chown: неверное имя владельца или группы')
        if separator and not group:
            raise CommandError('chown: группа не задана')
        return owner, group if separator else None
    def chown(self, arguments):
        flags, values = self.options(arguments, 'R')
        if len(values) < CHOWN_MIN_ARGUMENTS:
            raise CommandError('chown: требуется владелец и хотя бы один путь')
        owner, group = self.owner_values(values[0])
        paths = [self.vfs.resolve(value, self.current) for value in values[1:]]
        for path in paths:
            self.vfs.get(path)
        for path in paths:
            self.vfs.chown(path, owner, group, 'R' in flags)
        return ''
    def rmdir(self, arguments):
        flags, paths = self.options(arguments, 'p')
        if not paths:
            raise CommandError('rmdir: требуется хотя бы одна директория')
        for name in paths:
            path = self.vfs.resolve(name, self.current)
            self.vfs.rmdir(path, self.current)
            if 'p' in flags:
                path = posixpath.dirname(path)
                while path != '/':
                    self.vfs.rmdir(path, self.current)
                    path = posixpath.dirname(path)
        return ''