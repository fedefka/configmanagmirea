#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
./run.sh --vfs examples/vfs/minimal --log logs/minimal.xml --script examples/vfs-startup.txt
