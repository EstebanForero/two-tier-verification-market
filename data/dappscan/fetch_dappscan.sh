#!/usr/bin/env bash
# Sparse-fetch DAppSCAN-bytecode (~3 GB) OUTSIDE the repo. Dataset has no license: do not commit data or derived files.
set -euo pipefail; D=${1:-/workspace/data/dappscan}; mkdir -p "$D"; cd "$D"
[ -d repo ] || git clone -q --filter=blob:none --no-checkout https://github.com/InPlusLab/DAppSCAN repo
cd repo; git sparse-checkout set DAppSCAN-bytecode README.md; git checkout -q 66a56619c44770e05c2db600fa6468115ff0dcd5 2>/dev/null || git checkout -q
echo "DAppSCAN @ $(git rev-parse HEAD)"
