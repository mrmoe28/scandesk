#!/usr/bin/env bash
set -euo pipefail

APP_NAME="scandesk"
INSTALL_DIR="/opt/$APP_NAME"
BIN_LINK="/usr/local/bin/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/${APP_NAME}.desktop"
ICON_SIZE=256
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "======================================"
echo "  ScanDesk Installer"
echo "======================================"

# Must run as root for /opt and /usr/share
if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] Please run this installer as root (use sudo)."
   exit 1
fi

# 1. Detect system dependencies
echo "[1/6] Checking system dependencies..."
MISSING=()

command -v python3 >/dev/null 2>&1 || MISSING+=("python3")
command -v pip3   >/dev/null 2>&1 || MISSING+=("python3-pip")
command -v scanimage >/dev/null 2>&1 || MISSING+=("sane-utils")
command -v img2pdf >/dev/null 2>&1 || MISSING+=("img2pdf")

if ! python3 -c "import tkinter" 2>/dev/null; then
    MISSING+=("python3-tk")
fi

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo "[WARN] Missing system packages detected: ${MISSING[*]}"
    if command -v apt-get >/dev/null 2>&1; then
        echo "[INFO] Attempting automatic install via apt..."
        apt-get update -qq
        apt-get install -y -qq "${MISSING[@]}" 2>/dev/null || {
            echo "[WARN] Auto-install had issues. Please install manually:"
            echo "       sudo apt-get install ${MISSING[*]}"
        }
    elif command -v dnf >/dev/null 2>&1; then
        echo "[INFO] Attempting automatic install via dnf..."
        dnf install -y "${MISSING[@]}" 2>/dev/null || {
            echo "[WARN] Auto-install had issues. Please install manually:"
            echo "       sudo dnf install ${MISSING[*]}"
        }
    elif command -v pacman >/dev/null 2>&1; then
        echo "[INFO] Attempting automatic install via pacman..."
        pacman -Sy --noconfirm "${MISSING[@]}" 2>/dev/null || {
            echo "[WARN] Auto-install had issues. Please install manually:"
            echo "       sudo pacman -S ${MISSING[*]}"
        }
    else
        echo "[WARN] Could not detect package manager. Please install manually:"
        echo "       ${MISSING[*]}"
    fi
else
    echo "[OK] All system dependencies present."
fi

# 2. Install Python dependencies
echo "[2/6] Installing Python dependencies..."
pip3 install --quiet --break-system-packages -r "$SCRIPT_DIR/requirements.txt"
echo "[OK] Python dependencies installed."

# 3. Create install directory
echo "[3/6] Creating install directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/assets"

# 4. Copy application files
echo "[4/6] Copying application files..."
cp -f scandesk.py "$INSTALL_DIR/"
cp -f run-scandesk.sh "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/run-scandesk.sh"

# Copy assets
if [[ -d "assets" ]]; then
    cp -rf assets/* "$INSTALL_DIR/assets/" 2>/dev/null || true
fi

# Create wrapper script in /usr/local/bin
cat > "$BIN_LINK" << 'EOF'
#!/usr/bin/env bash
exec /opt/scandesk/run-scandesk.sh "$@"
EOF
chmod +x "$BIN_LINK"

echo "[OK] Application installed to $INSTALL_DIR"

# 5. Install .desktop file
echo "[5/6] Installing desktop entry..."
cp -f scandesk.desktop "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications/
fi

echo "[OK] Desktop entry installed."

# 6. Done
echo "[6/6] Installation complete!"
echo ""
echo "  Launch ScanDesk:"
echo "    From terminal:  scandesk"
echo "    From app menu:  Search for \"ScanDesk\""
echo ""
echo "  To uninstall later, run:"
echo "    sudo bash uninstall.sh"
echo ""
echo "======================================"
