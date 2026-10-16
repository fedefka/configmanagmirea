import argparse
from pathlib import Path
import xml.etree.ElementTree as element_tree
from datetime import datetime
PROJECT_ROOT = Path(__file__).resolve().parents[1]
def read_config(arguments=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--vfs',
        default=str(
            PROJECT_ROOT /
            'examples/vfs/minimal'))
    parser.add_argument(
        '--log',
        default=str(
            PROJECT_ROOT /
            'logs/commands.xml'))
    parser.add_argument('--script')
    return parser.parse_args(arguments)
class CommandLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.root = element_tree.Element('events')
        self.save()
    def save(self):
        element_tree.ElementTree(self.root).write(self.path, encoding='utf-8',
                                                  xml_declaration=True)
    def record(self, command, error=''):
        event = element_tree.SubElement(self.root, 'event')
        timestamp = datetime.now().isoformat(timespec='seconds')
        element_tree.SubElement(event, 'datetime').text = timestamp
        element_tree.SubElement(event, 'command').text = command
        element_tree.SubElement(event, 'error').text = error
        self.save()
