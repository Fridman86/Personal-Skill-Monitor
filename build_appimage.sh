#!/bin/bash
set -e

# Configuration
APP_NAME="PersonalSkillMonitor"
VERSION="0.3.1"
DIST_DIR="dist"
BUILD_DIR="build"

echo "Building AppImage for $APP_NAME v$VERSION using PyInstaller + linuxdeploy..."

# Clean up
rm -rf "$DIST_DIR" "$BUILD_DIR" PersonalSkillMonitor.spec
mkdir -p "$DIST_DIR"

# Ensure venv exists and has dependencies
VENV="./.venv"
if [ ! -d "$VENV" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
fi

echo "Installing build dependencies..."
"$VENV/bin/pip" install pyinstaller requests python-dotenv Pillow

echo "Resizing icon..."
"$VENV/bin/python3" -c "from PIL import Image; img = Image.open('src/gui/assets/icon.png'); img = img.resize((256, 256), Image.Resampling.LANCZOS); img.save('icon.png')"

echo "Running PyInstaller..."
# Note: we use --onedir to let linuxdeploy handle the final bundling and compression
"$VENV/bin/pyinstaller" --noconfirm --onedir --windowed \
    --name "$APP_NAME" \
    --add-data "src:src" \
    --add-data "config.env:." \
    --add-data "src/gui/assets/icon.png:." \
    --hidden-import "PIL._tkinter_finder" \
    main.py

# Prepare for linuxdeploy
APPDIR="AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

# Copy PyInstaller output to AppDir
cp -r "dist/$APP_NAME/." "$APPDIR/usr/bin/"

# Run linuxdeploy
# We use the binary produced by PyInstaller as the main executable
export VERSION=$VERSION
linuxdeploy --appdir "$APPDIR" \
    --executable "$APPDIR/usr/bin/$APP_NAME" \
    --desktop-file PersonalSkillMonitor.desktop \
    --icon-file icon.png \
    --output appimage

# Final cleanup and move
mv *.AppImage "$DIST_DIR/PersonalSkillMonitor-x86_64.AppImage"

echo "Build complete! AppImage is in $DIST_DIR/"
