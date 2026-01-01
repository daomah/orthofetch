#!/bin/sh
set -e

BIN_DIR="$HOME/.local/bin"
DATA_DIR="$HOME/.local/share/orthofetch"

mkdir -p "$BIN_DIR"
mkdir -p "$DATA_DIR"

# Download main script
curl -fsSL https://raw.githubusercontent.com/roguehashrate/orthofetch/main/orthofetch.py -o "$BIN_DIR/orthofetch"
chmod +x "$BIN_DIR/orthofetch"

# Download data files
curl -fsSL https://raw.githubusercontent.com/roguehashrate/orthofetch/main/data/orthodox_calendar_2026.txt -o "$DATA_DIR/orthodox_calendar_2026.txt"

echo "[*] Installation complete!"
echo "Run 'orthofetch' from anywhere."
echo "Orthofetch script intalled to $BIN_DIR."
echo "Data installed to $DATA_DIR."
