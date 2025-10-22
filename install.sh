#!/bin/bash
# KdG-Kiosk Quick Installer
# This script downloads and runs the Python installer

set -e

echo "================================================"
echo "  KdG-Kiosk Quick Installer"
echo "================================================"
echo ""

# Check if running on Linux
if [ "$(uname)" != "Linux" ]; then
    echo "Error: This installer only works on Linux systems."
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Install it with: sudo apt install python3"
    exit 1
fi

# Download the installer
INSTALLER_URL="https://kdg-kiosk.web.app/install-kdg-kiosk.py"
TEMP_DIR=$(mktemp -d)
INSTALLER_PATH="$TEMP_DIR/install-kdg-kiosk.py"

echo "Downloading KdG-Kiosk installer..."
if command -v wget &> /dev/null; then
    wget -q -O "$INSTALLER_PATH" "$INSTALLER_URL"
elif command -v curl &> /dev/null; then
    curl -s -o "$INSTALLER_PATH" "$INSTALLER_URL"
else
    echo "Error: Neither wget nor curl is installed."
    echo "Install one with: sudo apt install wget"
    exit 1
fi

# Make it executable
chmod +x "$INSTALLER_PATH"

# Run the installer
echo ""
echo "Starting installation..."
echo ""
python3 "$INSTALLER_PATH"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "================================================"
echo "  Installation complete!"
echo "================================================"

