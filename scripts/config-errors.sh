#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
./run.sh --unknown || true
./run.sh --script examples/missing.txt || true
./run.sh --log /dev/null/commands.xml || true
