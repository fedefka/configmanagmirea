import sys
from pathlib import Path

from config import CommandLog, read_config
from gui import ShellWindow
from shell import Shell


def main():
    config = read_config()
    try:
        logger = CommandLog(config.log)
        window = ShellWindow(Shell(), Path(config.vfs).name or 'VFS', logger)
        window.write('VFS: ' + config.vfs)
        window.write('Лог: ' + config.log)
        window.write('Стартовый скрипт: ' + (config.script or 'не задан'))
        if config.script:
            window.run_script(config.script)
        if not window.shell.closed:
            window.run()
    except (OSError, UnicodeError) as error:
        print('Ошибка: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
