import os
import shlex
VFS_NAME = "VFS"
MAX_PATH_ARGUMENTS = 1
class CommandError(Exception):
    pass
def parse_command(line):
    try:
        arguments = shlex.split(line)
    except ValueError as error:
        raise CommandError("Неверные кавычки: " + str(error)) from error
    return [os.path.expandvars(argument) for argument in arguments]
class Shell:
    def __init__(self, vfs=None):
        self.closed = False
        self.vfs = vfs
        self.current = "/"
    def execute(self, line):
        parts = parse_command(line)
        if not parts:
            return ""
        command, arguments = parts[0], parts[1:]
        if command == "exit":
            if arguments:
                raise CommandError("exit: аргументы не поддерживаются")
            self.closed = True
            return "Завершение работы"
        if command not in ("ls", "cd"):
            raise CommandError("Неизвестная команда: " + command)
        if len(arguments) > MAX_PATH_ARGUMENTS:
            raise CommandError(command + ": ожидается не более одного пути")
        return command + ": аргументы " + repr(arguments)
