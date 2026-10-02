#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
./run.sh --vfs examples/vfs/deep --log logs/deep.xml --script examples/vfs-startup.txt
