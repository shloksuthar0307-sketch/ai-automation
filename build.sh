#!/usr/bin/env bash
# ==============================================================================
# Render Build Script for Sitewright
# ==============================================================================
# This script is executed during the Render build phase.
# It ensures all dependencies, static files, and database migrations are ready.
# ==============================================================================

# Exit immediately if any command returns a non-zero exit status
set -o errexit

echo "==> [Render Build] Upgrading pip..."
python -m pip install --upgrade pip

echo "==> [Render Build] Installing Python packages from requirements.txt..."
python -m pip install --no-cache-dir -r requirements.txt

echo "==> [Render Build] Collecting static assets for WhiteNoise..."
python manage.py collectstatic --noinput

echo "==> [Render Build] Applying database migrations..."
python manage.py migrate --noinput

echo "==> [Render Build] Build completed successfully!"

