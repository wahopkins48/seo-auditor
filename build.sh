#!/usr/bin/env bash
set -o errexit

ROOT="$(cd "$(dirname "$0")" && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="$ROOT/.playwright-browsers"

mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"

python -m pip install --upgrade pip
pip install -r requirements.txt

python -m playwright install chromium
