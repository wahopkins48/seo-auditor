#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install Python packages
pip install -r requirements.txt

# 2. Install Playwright and its specific dependencies
# (Playwright's internal command is allowed on Render)
playwright install chromium
playwright install-deps