#!/usr/bin/env bash
# Fetch SmartBugs Curated at the pinned commit into data/raw/smartbugs-curated (gitignored).
set -euo pipefail; cd "$(dirname "$0")/.."; source smartbugs.lock
mkdir -p raw; [ -d raw/smartbugs-curated ] || git clone -q "$repo" raw/smartbugs-curated
git -C raw/smartbugs-curated fetch -q origin "$commit" 2>/dev/null || true; git -C raw/smartbugs-curated checkout -q "$commit"
echo "smartbugs-curated @ $(git -C raw/smartbugs-curated rev-parse HEAD)"
