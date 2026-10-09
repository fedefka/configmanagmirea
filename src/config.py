import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime
def read_config(arguments=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--vfs', default='examples/vfs/minimal')
    parser.add_argument('--log', default='logs/commands.xml')
    parser.add_argument('--script')
    return parser.parse_args(arguments)
class CommandLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.root = ET.Element('events')
        self.save()
    def save(self):
        ET.ElementTree(self.root).write(self.path, encoding='utf-8',
                                       xml_declaration=True)
    def record(self, command, error=''):
        event = ET.SubElement(self.root, 'event')
        ET.SubElement(event, 'datetime').text = datetime.now().isoformat(timespec='seconds')
        ET.SubElement(event, 'command').text = command
        ET.SubElement(event, 'error').text = error
        self.save()
