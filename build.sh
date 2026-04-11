#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for WeasyPrint and Playwright
apt-get update && apt-get install -y \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0

pip install -r requirements.txt

# Install playwright and its system dependencies
playwright install --with-deps chromium