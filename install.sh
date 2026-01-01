#!/bin/sh
# install.sh - Install Orthodox Calendar CLI

set -e

# Define target locations
BIN_DIR="$HOME/.local/bin"
DATA_DIR="$HOME/.local/share/orthofetch"
SCRIPT_NAME="orthofetch.py"
EXECUTABLE_NAME="orthofetch"

echo "[*] Installing Orthofetch..."

# Create directories if they don't exist
mkdir -p "$BIN_DIR"
mkdir -p "$DATA_DIR"

# Copy the main script and make it executable
install -m 755 "$SCRIPT_NAME" "$BIN_DIR/$EXECUTABLE_NAME"

# Copy the data folder if it exists
if [ -d "data" ]; then
    cp -r data/* "$DATA_DIR/"
fi

echo "[*] Installation complete!"
echo "You can now run '$EXECUTABLE_NAME' from anywhere."
echo "Data files installed to $DATA_DIR"
echo "Ensure $BIN_DIR is in your PATH if you can't run it directly."
