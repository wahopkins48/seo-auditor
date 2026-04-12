#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install system dependencies for the PDF engine (WeasyPrint)
apt-get update && apt-get install -y \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0

# 2. Install Python packages
pip install -r requirements.txt

# 3. Install the browser and its specific Linux dependencies
playwright install --with-deps chromium