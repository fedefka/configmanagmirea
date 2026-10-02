#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
./run.sh --vfs examples/vfs/missing || true
./run.sh --vfs examples/vfs/minimal/hello.txt || true
