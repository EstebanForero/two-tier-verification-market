#!/bin/sh
# SolidiFI benchmark: contracts retain their original Etherscan licenses -> data stays OUTSIDE the repo.
set -e; D=${SOLIDIFI_DIR:-/workspace/data/solidifi}
[ -d "$D/.git" ] || git clone https://github.com/smartbugs/SolidiFI-benchmark "$D"
git -C "$D" checkout -q 4b0573e1b3f7031396de6f48f7f3e7380222ad3a
