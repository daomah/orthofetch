# orthofetch

A terminal-based Orthodox Christian calendar made in a "fetch" style for Linux, showing today's saints, feasts, fasting, and readings.

---

## Install

Run this one-liner:

```bash
/bin/sh -c "$(curl -fsSL https://raw.githubusercontent.com/daomah/orthofetch/main/install.sh)"
```

This will:

- Copy the `orthofetch` script to `~/.local/bin`
- Copy the calendar data to `~/.local/share/orthofetch`
- Copy the bible data to `~/.local/share/orthofetch/bible`

Make sure `~/.local/bin` is in your `PATH` to run `orthofetch` from anywhere.

---

## Usage

### Daily Calendar

Simply run:

```bash
orthofetch
```

It will display today's Orthodox calendar entry in a neat, aligned format with the Orthodox cross.

```bash
orthofetch --reading [NUM]
```

This will give you the full text of a specific reading for today. So if you see [1] John 3.15-18 for example you will get those verses to read.

### Bible Reading

```bash
orthofetch --bible
```

This will display all available Bible books organized by testament.

**Updated Command Features:**

- **Multi-word book support**: `--bible "1 Kings" 3.1-5` works perfectly
- **Forgiving book names**: case-insensitive, with aliases (`--bible psalm 23`, `--bible john 3:16`); quoting multi-word names is optional
- **Cross-chapter and single-chapter references**: `--bible Job 2:13-4:3`, `--bible Jude 1-10`
- **Format flexibility**: Supports both dot (`3.1-5`) and colon (`3:1-5`) verse references
- **Complete reference options**: Single verse, verse ranges, full chapters
- **Deuterocanonical support**: `--bible "4 Maccabees"` and all deuterocanonical books
- **JSON-based structure**: Fast loading from JSON files instead of text files

```bash
orthofetch --bible [BOOK]
```

This will list all chapters in the specified book (e.g., `--bible John`).

```bash
orthofetch --bible [BOOK] [CHAPTER]
```

This will display the full chapter (e.g., `--bible John 3`).

```bash
orthofetch --bible [BOOK] [CHAPTER]:[VERSE]
```

This will display a specific verse (e.g., `--bible John 3:16`).

```bash
orthofetch --bible [BOOK] [CHAPTER]:[VERSE]-[VERSE]
```

This will display a range of verses (e.g., `--bible John 3:16-17`).

Multi-word book names must be quoted:

```bash
orthofetch --bible "1 Kings" 3:1-5
orthofetch --bible "Wisdom of Solomon" 7
```

### Random Verses

```bash
orthofetch --random-verse
```

This will display a random verse from anywhere in the Bible.

```bash
orthofetch --random-verse [BOOK]
```

This will display a random verse from the specified book (e.g., `--random-verse Proverbs`).

### Display Options

```bash
orthofetch --no-color
```

This will take the color out of it making it plain text. This will also work with all other commands if you want to use it that way.

---

## Tests

```bash
python3 -m unittest discover -s tests -v
```

---

## Data

-

Books come from the JSON files from [l1lsm0k13's AncientBible project](https://l1lsm0k13.github.io/AncientBible/).

Calendar comes from [orthocal](https://orthocal.info/).

:)

---

## License

BSD 2-Clause

## Configuration

- `ORTHOFETCH_DATA`: directory holding `orthodox_calendar_YEAR.txt` and `bible/` (default: `data/` next to the script, else `~/.local/share/orthofetch`).
- `NO_COLOR`: disables colour; colour is also disabled automatically when output is not a terminal.
- `ORTHOFETCH_FORCE=1`: make the installer re-download data files that already exist.
