#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pip download --only-binary=:all: --dest vendor/wheels -r requirements.txt
python3 -m pip hash vendor/wheels/* > vendor/WHEEL_HASHES.txt
