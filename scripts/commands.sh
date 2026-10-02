#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p examples/vfs/deep/empty examples/vfs/deep/remove/parent/leaf
./run.sh --vfs examples/vfs/deep --log logs/commands.xml --script examples/all-commands.txt
