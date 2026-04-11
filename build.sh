#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for WeasyPrint
apt-get update && apt-get install -y \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser and its specific system dependencies
playwright install --with-deps chromium