#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 build_defihacklabs.py
python3 build_solidifi.py
python3 build_presumed_safe.py
python3 build_solodit.py || true
python3 merge.py
