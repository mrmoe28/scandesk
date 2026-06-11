#!/usr/bin/env bash
set -euo pipefail

APP_NAME="scandesk"
INSTALL_DIR="/opt/$APP_NAME"
BIN_LINK="/usr/local/bin/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/${APP_NAME}.desktop"

echo "======================================"
echo "  ScanDesk Uninstaller"
echo "======================================"

if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] Please run as root (use sudo)."
   exit 1
fi

echo "[1/4] Removing binary symlink..."
rm -f "$BIN_LINK"
echo "[OK]"

echo "[2/4] Removing desktop entry..."
rm -f "$DESKTOP_FILE"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications/ 2>/dev/null || true
fi
echo "[OK]"

echo "[3/4] Removing application files..."
rm -rf "$INSTALL_DIR"
echo "[OK]"

echo "[4/4] Cleaning up..."
# Remove cached bytecode
find /home -path "*/__pycache__/scandesk*" -delete 2>/dev/null || true

echo ""
echo "[DONE] ScanDesk has been removed from your system."
echo "======================================"
