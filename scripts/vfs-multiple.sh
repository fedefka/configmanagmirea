#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
./run.sh --vfs examples/vfs/multiple --log logs/multiple.xml --script examples/vfs-startup.txt
