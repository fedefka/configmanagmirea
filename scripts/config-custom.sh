#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
./run.sh --vfs examples/vfs/minimal --log logs/custom.xml --script examples/startup.txt
