#!/bin/sh
set -e

BIN_DIR="$HOME/.local/bin"
DATA_DIR="$HOME/.local/share/orthofetch"

mkdir -p "$BIN_DIR"
mkdir -p "$DATA_DIR"

# Download main script (always update to get latest version)
echo "Downloading orthofetch script..."
curl -fsSL https://raw.githubusercontent.com/daomah/orthofetch/main/orthofetch.py -o "$BIN_DIR/orthofetch"
chmod +x "$BIN_DIR/orthofetch"

# Download calendar data if not exists
if [ ! -f "$DATA_DIR/orthodox_calendar_2026.txt" ]; then
    echo "Downloading calendar data..."
    curl -fsSL https://raw.githubusercontent.com/daomah/orthofetch/main/data/orthodox_calendar_2026.txt -o "$DATA_DIR/orthodox_calendar_2026.txt"
else
    echo "Calendar data already exists, skipping download."
fi

# Create bible directory and download all Bible files
BIBLE_DIR="$DATA_DIR/bible"
mkdir -p "$BIBLE_DIR"

# Check for old folder-based structure and remove it if exists
if [ -d "$BIBLE_DIR/GEN" ] || [ -d "$BIBLE_DIR/EXO" ] || [ -d "$BIBLE_DIR/LEV" ]; then
    echo "Found old folder-based Bible structure, removing..."
    rm -rf "$BIBLE_DIR"/*
    echo "Old structure removed."
fi

echo "Installing Bible data to $BIBLE_DIR/"
echo ""

# Function to download Bible books as JSON files
download_bible_book() {
    local book_code=$1
    local book_name=$2
    local json_filename=$3
    local url="https://raw.githubusercontent.com/daomah/orthofetch/main/data/bible/$json_filename"
    local file="$BIBLE_DIR/$json_filename"
    
    # Check if file already exists
    if [ -f "$file" ]; then
        echo "  ✓ $book_name (already exists)"
        return
    fi
    
    # Try to download the JSON file
    if curl -fsSL "$url" -o "$file" 2>/dev/null; then
        echo "  ✓ $book_name"
    else
        echo "  ✗ Failed to download $book_name"
        rm -f "$file"  # Remove empty file if download failed
    fi
}

echo "Starting Bible data download..."
echo "This may take a few minutes as we download 73 Bible books..."
echo ""

# Download all Bible JSON files
download_bible_book "GEN" "Genesis" "genesis.json"
download_bible_book "EXO" "Exodus" "exodus.json"
download_bible_book "LEV" "Leviticus" "leviticus.json"
download_bible_book "NUM" "Numbers" "numbers.json"
download_bible_book "DEU" "Deuteronomy" "deuteronomy.json"
download_bible_book "JOS" "Joshua" "joshua.json"
download_bible_book "JDG" "Judges" "judges.json"
download_bible_book "RUT" "Ruth" "ruth.json"
download_bible_book "1SA" "1 Samuel" "1samuel.json"
download_bible_book "2SA" "2 Samuel" "2samuel.json"
download_bible_book "1KI" "1 Kings" "1kings.json"
download_bible_book "2KI" "2 Kings" "2kings.json"
download_bible_book "1CH" "1 Chronicles" "1chronicles.json"
download_bible_book "2CH" "2 Chronicles" "2chronicles.json"
download_bible_book "1ES" "1 Ezra" "1ezra.json"
download_bible_book "2ES" "2 Ezra" "2ezra.json"
download_bible_book "NEH" "Nehemiah" "nehemiah.json"
download_bible_book "EST" "Esther" "esther.json"
download_bible_book "JOB" "Job" "job.json"
download_bible_book "PSA" "Psalms" "psalms.json"
download_bible_book "PRO" "Proverbs" "proverbs.json"
download_bible_book "ECC" "Ecclesiastes" "ecclesiastes.json"
download_bible_book "SNG" "Song of Solomon" "songs.json"
download_bible_book "ISA" "Isaiah" "isaiah.json"
download_bible_book "JER" "Jeremiah" "jeremiah.json"
download_bible_book "LAM" "Lamentations" "lamentations.json"
download_bible_book "EZK" "Ezekiel" "ezekiel.json"
download_bible_book "DAN" "Daniel" "daniel.json"
download_bible_book "HOS" "Hosea" "hosea.json"
download_bible_book "JOL" "Joel" "joel.json"
download_bible_book "AMO" "Amos" "amos.json"
download_bible_book "OBA" "Obadiah" "obadiah.json"
download_bible_book "JON" "Jonah" "jonah.json"
download_bible_book "MIC" "Micah" "micah.json"
download_bible_book "NAM" "Nahum" "nahum.json"
download_bible_book "HAB" "Habakkuk" "habakkuk.json"
download_bible_book "ZEP" "Zephaniah" "zephaniah.json"
download_bible_book "HAG" "Haggai" "haggai.json"
download_bible_book "ZEC" "Zechariah" "zechariah.json"
download_bible_book "MAL" "Malachi" "malachi.json"
download_bible_book "MAT" "Matthew" "matthew.json"
download_bible_book "MRK" "Mark" "mark.json"
download_bible_book "LUK" "Luke" "luke.json"
download_bible_book "JHN" "John" "john.json"
download_bible_book "ACT" "Acts" "acts.json"
download_bible_book "ROM" "Romans" "romans.json"
download_bible_book "1CO" "1 Corinthians" "1corinthians.json"
download_bible_book "2CO" "2 Corinthians" "2corinthians.json"
download_bible_book "GAL" "Galatians" "galatians.json"
download_bible_book "EPH" "Ephesians" "ephesians.json"
download_bible_book "PHP" "Philippians" "philippians.json"
download_bible_book "COL" "Colossians" "colossians.json"
download_bible_book "1TH" "1 Thessalonians" "1thessalonians.json"
download_bible_book "2TH" "2 Thessalonians" "2thessalonians.json"
download_bible_book "1TI" "1 Timothy" "1timothy.json"
download_bible_book "2TI" "2 Timothy" "2timothy.json"
download_bible_book "TIT" "Titus" "titus.json"
download_bible_book "PHM" "Philemon" "philemon.json"
download_bible_book "HEB" "Hebrews" "hebrews.json"
download_bible_book "JAS" "James" "james.json"
download_bible_book "1PE" "1 Peter" "1peter.json"
download_bible_book "2PE" "2 Peter" "2peter.json"
download_bible_book "1JO" "1 John" "1john.json"
download_bible_book "2JO" "2 John" "2john.json"
download_bible_book "3JO" "3 John" "3john.json"
download_bible_book "JUD" "Jude" "jude.json"
download_bible_book "REV" "Revelation" "revelation.json"

# Download Deuterocanonical books
download_bible_book "TOB" "Tobit" "tobit.json"
download_bible_book "JDT" "Judith" "judith.json"
download_bible_book "WIS" "Wisdom of Solomon" "wisdom.json"
download_bible_book "SIR" "Sirach" "sirach.json"
download_bible_book "BAR" "Baruch" "baruch.json"
download_bible_book "1MA" "1 Maccabees" "1maccabees.json"
download_bible_book "2MA" "2 Maccabees" "2maccabees.json"

# Download additional deuterocanonical books
download_bible_book "3MA" "3 Maccabees" "3maccabees.json"
download_bible_book "4MA" "4 Maccabees" "4maccabees.json"
download_bible_book "ESG" "Esther (Greek)" "esther_greek.json"
download_bible_book "P151" "Psalm 151" "psalm151.json"
download_bible_book "MAN" "Prayer of Manasseh" "manasseh.json"

echo ""
echo "[*] Installation complete!"
echo "Run 'orthofetch' from anywhere."
echo "Orthofetch script installed to $BIN_DIR."
echo "Data installed to $DATA_DIR."
