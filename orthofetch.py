#!/usr/bin/env python3
import argparse
import datetime
import functools
import json
import os
import random
import re
import socket
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request

# Global variable for color control
no_color = False

# Color scheme for Orthodox Christian theme


class Colors:
    # ANSI color codes
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Colors
    GOLD = '\033[38;5;214m'      # Gold for cross and special elements
    DEEP_RED = '\033[38;5;88m'    # Deep red for feast days
    BLUE = '\033[38;5;25m'        # Deep blue for saints
    GREEN = '\033[38;5;28m'       # Green for fasting info
    PURPLE = '\033[38;5;91m'      # Purple for readings
    CYAN = '\033[38;5;39m'        # Cyan for labels
    WHITE = '\033[38;5;255m'      # White for text
    GRAY = '\033[38;5;245m'       # Gray for subtle elements


def _find_data_dir() -> str:
    """Locate the data directory: $ORTHOFETCH_DATA, then ./data next to this script, then ~/.local/share."""
    env = os.environ.get("ORTHOFETCH_DATA")
    if env:
        return os.path.expanduser(env)
    script_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if os.path.isdir(os.path.join(script_data, "bible")):
        return script_data
    return os.path.expanduser("~/.local/share/orthofetch")


DATA_DIR = _find_data_dir()
CALENDAR_FILE = os.path.join(DATA_DIR, f"orthodox_calendar_{datetime.date.today().year}.txt")
BIBLE_DIR = os.path.join(DATA_DIR, "bible")

# Book name to 3-letter code mapping
BOOK_CODES = {
    "Genesis": "GEN", "Exodus": "EXO", "Leviticus": "LEV", "Numbers": "NUM", "Deuteronomy": "DEU",
    "Joshua": "JOS", "Judges": "JDG", "Ruth": "RUT", "1 Samuel": "1SA", "2 Samuel": "2SA",
    "1 Kings": "1KI", "2 Kings": "2KI", "1 Chronicles": "1CH", "2 Chronicles": "2CH",
    "Nehemiah": "NEH", "Esther": "EST", "Job": "JOB", "Psalms": "PSA", "Proverbs": "PRO",
    "Ecclesiastes": "ECC", "Song of Solomon": "SNG", "Isaiah": "ISA", "Jeremiah": "JER",
    "Lamentations": "LAM", "Ezekiel": "EZK", "Daniel": "DAN", "Hosea": "HOS", "Joel": "JOL",
    "Amos": "AMO", "Obadiah": "OBA", "Jonah": "JON", "Micah": "MIC", "Nahum": "NAM",
    "Habakkuk": "HAB", "Zephaniah": "ZEP", "Haggai": "HAG", "Zechariah": "ZEC", "Malachi": "MAL",
    "Matthew": "MAT", "Mark": "MRK", "Luke": "LUK", "John": "JHN", "Acts": "ACT",
    "Romans": "ROM", "1 Corinthians": "1CO", "2 Corinthians": "2CO", "Galatians": "GAL",
    "Ephesians": "EPH", "Philippians": "PHP", "Colossians": "COL", "1 Thessalonians": "1TH",
    "2 Thessalonians": "2TH", "1 Timothy": "1TI", "2 Timothy": "2TI", "Titus": "TIT",
    "Philemon": "PHM", "Hebrews": "HEB", "James": "JAS", "1 Peter": "1PE", "2 Peter": "2PE",
    "1 John": "1JN", "2 John": "2JN", "3 John": "3JN", "Jude": "JUD", "Revelation": "REV",
    "Wisdom of Solomon": "WIS", "Sirach": "SIR", "Baruch": "BAR", "1 Maccabees": "1MA", "2 Maccabees": "2MA",
    "3 Maccabees": "3MA", "4 Maccabees": "4MA", "Tobit": "TOB", "Judith": "JDT", "Esther (Greek)": "ESG",
    "Psalm 151": "P151", "Prayer of Manasseh": "MAN", "1 Ezra": "1ES", "2 Ezra": "2ES",
    "Epistle of Jeremiah": "LJE"
}

CODE_TO_NAME = {code: name for name, code in BOOK_CODES.items()}

# Case-insensitive lookup by full name, 3-letter code, or common alias
_BOOK_LOOKUP = {name.lower(): name for name in BOOK_CODES}
_BOOK_LOOKUP.update({code.lower(): name for code, name in CODE_TO_NAME.items()})
_BOOK_LOOKUP.update({
    "psalm": "Psalms", "song of songs": "Song of Solomon", "songs": "Song of Solomon",
    "wisdom": "Wisdom of Solomon", "ecclesiasticus": "Sirach", "revelations": "Revelation",
    "apocalypse": "Revelation", "esther greek": "Esther (Greek)",
})

# Books with a single chapter: "Jude 1-10" means verses 1-10, not chapters
SINGLE_CHAPTER_BOOKS = {"Obadiah", "Philemon", "2 John", "3 John", "Jude", "Epistle of Jeremiah"}

# Names whose JSON filename can't be derived by rule
_FILENAME_OVERRIDES = {
    "Wisdom of Solomon": "wisdom", "Song of Solomon": "songs", "Esther (Greek)": "esther_greek",
    "Psalm 151": "psalm151", "Prayer of Manasseh": "manasseh", "Epistle of Jeremiah": "epistle",
}


def resolve_book(name: str) -> str | None:
    """Return the canonical book name for a case-insensitive name, code or alias, else None.

    >>> resolve_book("john")
    'John'
    >>> resolve_book("1 kings")
    '1 Kings'
    >>> resolve_book("Psalm")
    'Psalms'
    """
    return _BOOK_LOOKUP.get(re.sub(r'\s+', ' ', name.strip()).lower())


# Compact Orthodox Cross (will be colored with gold)
ORTHODOX_CROSS = [
    "      ██",
    "    ██████",
    "      ██",
    "  ██████████",
    "      ██",
    "      ██",
    "    ████",
    "      ████",
    "      ██"
]

TEXT_GAP = 8
WRAP_WIDTH = 60

FIELDS = ["[Saints]:", "[Feasts]:", "[Fasting]:", "[Readings]:"]
MAX_FIELD_WIDTH = max(len(f) for f in FIELDS)
CROSS_WIDTH = max(len(line) for line in ORTHODOX_CROSS)


def bible_filename(book_name: str) -> str:
    """Return the JSON filename stem for a book name (without .json extension).

    >>> bible_filename("1 Kings")
    '1kings'
    >>> bible_filename("Wisdom of Solomon")
    'wisdom'
    >>> bible_filename("Esther (Greek)")
    'esther_greek'
    >>> bible_filename("Psalm 151")
    'psalm151'
    """
    if book_name in _FILENAME_OVERRIDES:
        return _FILENAME_OVERRIDES[book_name]
    stem = book_name.lower().replace(' ', '_').replace('of_solomon', '')
    if stem.startswith(('1_', '2_', '3_')):
        return stem.replace('_', '')
    if 'wisdom' in stem:
        return 'wisdom'
    if 'song' in stem:
        return 'songs'
    if 'esther_(greek)' in stem:
        return 'esther_greek'
    return stem


def _parse_chapter_verse(ref: str) -> tuple[int, int, int]:
    """Parse 'chapter:verse[-end]' or 'chapter.verse[-end]'.

    Returns (chapter, start_verse, end_verse). Raises ValueError on bad input.
    """
    ref = ref.replace('.', ':')
    chapter_part, verse_part = ref.split(':', 1)
    chapter = int(chapter_part)
    if '-' in verse_part:
        start_v, end_v = verse_part.split('-', 1)
        return chapter, int(start_v), int(end_v)
    v = int(verse_part)
    return chapter, v, v


def parse_reading_reference(reference: str) -> tuple[str, int, int | None, int, int | None] | None:
    """Parse a calendar reading reference string.

    Handles formats: 'Genesis 3:1-8', 'Exodus 15.22-16.1', '3[1] Kings 2.6-14',
    'Numbers 8', 'Exodus 12, 13' (consecutive chapters only), 'Jude 1-10'.

    Returns None on failure, or (book, start_chapter, start_verse, end_chapter, end_verse)
    where start_verse/end_verse may be None for chapter-only references.
    """
    # Handle special case for Wisdom of Solomon
    if reference.startswith('Wisdom ') and not reference.startswith('Wisdom of '):
        reference = 'Wisdom of Solomon' + reference[6:]

    # Handle special format like "3[1] Kings 2.6-14" - extract the second number in brackets
    reference = normalize_reference(reference)

    # Convert dots to colons for consistency (but keep original for parsing cross-chapter ranges)
    reference_clean = reference.replace('.', ':')

    # Check for cross-chapter pattern: Book Chapter:Verse-Chapter:Verse
    cross_chapter_pattern = r"([0-9A-Za-z\s()]+)\s+(\d+)[:](\d+)[-:](\d+)[:](\d+)$"
    cross_match = re.match(cross_chapter_pattern, reference_clean.strip())

    if cross_match:
        book = cross_match.group(1).strip()
        start_chapter = int(cross_match.group(2))
        start_verse = int(cross_match.group(3))
        end_chapter = int(cross_match.group(4))
        end_verse = int(cross_match.group(5))

        return book, start_chapter, start_verse, end_chapter, end_verse

    # Pattern to match: Book Chapter:Verse-Verse or Book Chapter:Verse (single chapter)
    single_chapter_pattern = r"([0-9A-Za-z\s()]+)\s+(\d+)[:](\d+)(?:[-:]?(\d+))?"
    match = re.match(single_chapter_pattern, reference_clean.strip())

    if match:
        book = match.group(1).strip()
        chapter = int(match.group(2))
        start_verse = int(match.group(3))
        end_verse = int(match.group(4)) if match.group(4) else start_verse

        # Return in 5-tuple format for consistency (start_chapter = end_chapter)
        return book, chapter, start_verse, chapter, end_verse

    # Single-chapter books: "Jude 1-10" is a verse range
    verse_range_match = re.match(r"([0-9A-Za-z\s()]+?)\s+(\d+)-(\d+)$", reference_clean.strip())
    if verse_range_match and resolve_book(verse_range_match.group(1)) in SINGLE_CHAPTER_BOOKS:
        return (resolve_book(verse_range_match.group(1)), 1,
                int(verse_range_match.group(2)), 1, int(verse_range_match.group(3)))

    # Pattern to match: Book Chapter (no verses)
    chapter_only_pattern = r"([0-9A-Za-z\s()]+)\s+(\d+)$"
    chapter_match = re.match(chapter_only_pattern, reference.strip())

    if chapter_match:
        book = chapter_match.group(1).strip()
        chapter = int(chapter_match.group(2))

        # Return chapter-only reference - verse range will be determined later
        return book, chapter, None, chapter, None

    # Pattern to match: Book Chapter, Chapter (comma-separated chapters)
    comma_chapter_pattern = r"([0-9A-Za-z\s()]+)\s+(\d+),\s*(\d+)$"
    comma_chapter_match = re.match(comma_chapter_pattern, reference.strip())

    if comma_chapter_match:
        book = comma_chapter_match.group(1).strip()
        start_chapter = int(comma_chapter_match.group(2))
        end_chapter = int(comma_chapter_match.group(3))
        if end_chapter != start_chapter + 1:
            return None  # non-contiguous chapters; callers expand the list themselves

        # Return cross-chapter reference with no verses
        return book, start_chapter, None, end_chapter, None

    return None


_KINGS_RE = re.compile(r'\d+\s*\[(\d+)\]\s+Kings')


def normalize_kings(reference: str) -> str:
    """Convert LXX-style '3 [1] Kings' / '3[1] Kings' to '1 Kings'.

    >>> normalize_kings("3 [1] Kings 17.1-23")
    '1 Kings 17.1-23'
    """
    return _KINGS_RE.sub(r'\1 Kings', reference)


def normalize_reference(reference: str) -> str:
    """Normalise calendar quirks before parsing: '3 [1] Kings', trailing '(LXX)', 'Jeremiah (Baruch 3.35-4.4)'.

    >>> normalize_reference("Proverbs 12.23-13.9 (LXX)")
    'Proverbs 12.23-13.9'
    >>> normalize_reference("Jeremiah (Baruch 3.35-4.4)")
    'Baruch 3.35-4.4'
    """
    reference = normalize_kings(reference.strip())
    reference = re.sub(r'^Jeremiah \((Baruch [^)]*)\)$', r'\1', reference)
    return re.sub(r'\s*\((?:LXX|MT)\)$', '', reference)


_LEADING_BOOK = re.compile(r'^((?:\d\s)?[A-Za-z][A-Za-z ()]*?)\s+\d')


@functools.lru_cache(maxsize=8)
def load_book(book_name: str) -> dict:
    """Load and cache a book's JSON. Raises OSError / json.JSONDecodeError on failure."""
    json_file = os.path.join(BIBLE_DIR, f"{bible_filename(book_name)}.json")
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)


def available_book_codes() -> list[str]:
    """Return the codes of the books whose JSON file is present in BIBLE_DIR."""
    filename_to_code = {bible_filename(name): code for name, code in BOOK_CODES.items()}
    if not os.path.isdir(BIBLE_DIR):
        return []
    codes = (filename_to_code.get(f[:-5]) for f in os.listdir(BIBLE_DIR) if f.endswith('.json'))
    return [code for code in codes if code]


def get_last_verse_in_chapter(book_code: str, chapter: int) -> int:
    """Get the last verse number in a chapter"""
    book_name = CODE_TO_NAME.get(book_code, book_code)
    try:
        data = load_book(book_name)
    except (OSError, json.JSONDecodeError):
        return 0

    for chapter_data in data.get("chapters", []):
        if chapter_data.get("chapter") == chapter:
            verses = chapter_data.get("verses", [])
            if verses:
                return verses[-1].get("verse", 0)
    return 0


def get_bible_text(
    book: str,
    start_chapter: int,
    start_verse: int | None,
    end_chapter: int | None = None,
    end_verse: int | None = None,
) -> str:
    """Retrieve bible text for the specified reference. Supports cross-chapter ranges and chapter-only references."""
    book = resolve_book(book) or book
    book_code = BOOK_CODES.get(book)
    if not book_code:
        return f"Book '{book}' not found."

    # Backward compatibility: if end_chapter is None, assume a single-chapter range
    if end_chapter is None:
        end_chapter = start_chapter
        if end_verse is None:
            end_verse = start_verse

    # Chapter-only references cover the whole chapter(s)
    if start_verse is None:
        start_verse = 1
    if end_verse is None:
        end_verse = get_last_verse_in_chapter(book_code, end_chapter)

    try:
        data = load_book(book)
    except FileNotFoundError:
        return f"Book {book} not found."
    except (OSError, json.JSONDecodeError) as e:
        return f"Error reading {book} {start_chapter}:{start_verse}-{end_chapter}:{end_verse}: {e}"

    chapters = {ch.get("chapter"): ch for ch in data.get("chapters", [])}
    if end_chapter == start_chapter and start_chapter not in chapters:
        return f"Chapter {start_chapter} of {book} not found."

    verses = []
    for chapter_num in range(start_chapter, end_chapter + 1):
        low = start_verse if chapter_num == start_chapter else 1
        high = end_verse if chapter_num == end_chapter else None
        for verse_obj in chapters.get(chapter_num, {}).get("verses", []):
            verse_num = verse_obj.get("verse", 0)
            if verse_num >= low and (high is None or verse_num <= high):
                verses.append((verse_num, verse_obj.get("text", "")))

    if not verses:
        if end_chapter > start_chapter:
            msg = f"Verses {start_chapter}:{start_verse}-{end_chapter}:{end_verse} not found in {book}."
        else:
            msg = f"Verses {start_verse}-{end_verse} not found in {book} {start_chapter}."
        return colorize_text(msg, Colors.GRAY)

    full_end = start_verse == 1 and end_verse == get_last_verse_in_chapter(book_code, end_chapter)
    if end_chapter > start_chapter:
        if full_end:
            header = f"{book} {start_chapter}-{end_chapter}"
        else:
            header = f"{book} {start_chapter}:{start_verse}-{end_chapter}:{end_verse}"
    elif full_end:
        header = f"{book} {start_chapter}"
    else:
        header = f"{book} {start_chapter}:{start_verse}"
        if end_verse != start_verse:
            header += f"-{end_verse}"

    body = "\n".join(
        f"{colorize_text(str(num), Colors.CYAN)} {colorize_text(text, Colors.WHITE)}" for num, text in verses)
    return f"\n{colorize_text(header, Colors.GOLD)}\n{body}"


def clean_readings(text: str) -> list[str]:
    """Split a calendar [Readings] field into individual references.

    Strips 'Composite N - ' prefixes, splits composites on ';', and normalises '3 [1] Kings'.
    """
    readings = []
    for reading in (r.strip() for r in text.replace('\u200b', '').split(" • ")):
        if not reading:
            continue
        if reading.startswith("Composite"):
            reading = normalize_kings(re.sub(r'^Composite \d+ -\s*', '', reading))
            book = None
            for part in (p.strip() for p in reading.split(';')):
                if not part:
                    continue
                if book and re.match(r'^\d+[.:]', part):
                    part = f"{book} {part}"  # bookless continuation: "Micah 4.2-3; 6.2-5"
                else:
                    book_match = _LEADING_BOOK.match(part)
                    book = book_match.group(1) if book_match else book
                readings.append(part)
        else:
            readings.append(reading)
    return [normalize_kings(r) for r in readings if not r.isdigit()]


_CHAPTER_VERSE_PART = re.compile(r'^\d+[.:]\d+(?:-\d+(?:[.:]\d+)?)?$')
_VERSE_PART = re.compile(r'^(\d+)(?:-(\d+))?$')
_VERSE_TO_CHAPTER_PART = re.compile(r'^(\d+)-(\d+)[.:](\d+)$')
_CHAPTER_LIST = re.compile(r'^(.+?)\s+(\d+(?:\s*,\s*\d+)+)$')


def parse_multi_reference(reference: str) -> list[tuple[str, int, int | None, int, int | None]]:
    """Parse a comma-separated reference like 'Genesis 17.1-2, 4, 5-7, 3.1' into separate ranges.

    A bare number is a verse (or verse range) in the most recent chapter; 'C.V' starts a new chapter.
    Raises ValueError with a user-facing message on failure.
    """
    parts = [p.strip() for p in reference.split(',') if p.strip()]
    first = parse_reading_reference(parts[0]) if parts else None
    if not first or first[2] is None:
        raise ValueError(f"Could not parse reading reference: {parts[0] if parts else reference}")

    refs = [first]
    for part in parts[1:]:
        book, _, _, chapter, _ = refs[-1]
        verse_match = _VERSE_PART.match(part)
        to_chapter = _VERSE_TO_CHAPTER_PART.match(part)
        if to_chapter:  # "45-23.1": verse 45 of the current chapter through 23:1
            parsed = (book, chapter, int(to_chapter.group(1)), int(to_chapter.group(2)), int(to_chapter.group(3)))
        elif _CHAPTER_VERSE_PART.match(part):
            parsed = parse_reading_reference(f"{book} {part}")
        elif verse_match:
            first_verse = int(verse_match.group(1))
            parsed = (book, chapter, first_verse, chapter, int(verse_match.group(2) or first_verse))
        else:
            parsed = parse_reading_reference(part)
        if not parsed:
            raise ValueError(f"Could not parse reading reference: {part}")
        refs.append(parsed)
    return refs


def find_today_entry() -> dict | None:
    """Return today's calendar entry, or None. Exits with a message if the calendar file is missing."""
    if not os.path.exists(CALENDAR_FILE):
        sys.exit(f"Calendar file {CALENDAR_FILE} not found. Run 'orthofetch -u' to fetch it.")
    today = datetime.date.today()
    today_str = f"📅 {today:%A, %B} {today.day}, {today.year}"
    for key, entry in parse_calendar(CALENDAR_FILE).items():
        if key.startswith(today_str):
            return entry
    return None


def display_reading(reading_number):
    """Display the full text of a specific reading for today"""
    entry = find_today_entry()
    if not entry:
        print(colorize_text("No entry for today in the calendar.", Colors.GRAY))
        return

    readings_text = entry.get("[Readings]:", "")
    if not readings_text:
        print(colorize_text("No readings for today.", Colors.GRAY))
        return

    readings = clean_readings(readings_text)
    reading_idx = reading_number - 1
    if reading_idx < 0 or reading_idx >= len(readings):
        print(colorize_text(
            f"Reading number {reading_number} not found. "
            f"There are {len(readings)} readings today.", Colors.DEEP_RED))
        print(colorize_text("Available readings:", Colors.CYAN))
        for i, reading in enumerate(readings, 1):
            print(f"  {colorize_text(str(i), Colors.GOLD)}. {colorize_text(reading, Colors.PURPLE)}")
        return

    reading_ref = readings[reading_idx]

    # "Exodus 12, 14": a list of whole chapters
    chapter_list = _CHAPTER_LIST.match(reading_ref)
    if chapter_list and '.' not in reading_ref and ':' not in reading_ref:
        for chapter in re.split(r'\s*,\s*', chapter_list.group(2)):
            print(get_bible_text(chapter_list.group(1), int(chapter), None, int(chapter), None))
        return

    try:
        references = parse_multi_reference(reading_ref) if ',' in reading_ref else None
    except ValueError as e:
        print(colorize_text(str(e), Colors.DEEP_RED))
        return
    if references is None:
        parsed = parse_reading_reference(reading_ref)
        if not parsed:
            print(colorize_text(f"Could not parse reading reference: {reading_ref}", Colors.DEEP_RED))
            return
        references = [parsed]

    for book, start_chapter, start_verse, end_chapter, end_verse in references:
        print(get_bible_text(book, start_chapter, start_verse, end_chapter, end_verse))


def parse_calendar(file_path):
    calendar = {}
    with open(file_path, "r", encoding="utf-8") as f:
        current_date = None
        entry = {}
        for line in f:
            line = line.strip()
            if line.startswith("📅"):
                if current_date:
                    calendar[current_date] = entry
                current_date = line
                entry = {field: "" for field in FIELDS}
            elif any(line.startswith(field) for field in FIELDS):
                for field in FIELDS:
                    if line.startswith(field):
                        entry[field] = line[len(field):].strip()
                        break
        if current_date:
            calendar[current_date] = entry
    return calendar


def wrap_readings(text, width):
    readings = clean_readings(text)

    lines = []

    for i, reading in enumerate(readings, 1):
        # Add number prefix: [1] reading
        numbered_reading = f"[{i}] {reading}"
        wrapped = textwrap.wrap(
            numbered_reading,
            width=width - 2,
            subsequent_indent="  "  # Indent continuation lines
        )
        for j, line in enumerate(wrapped):
            if j == 0:
                lines.append("  " + line)
            else:
                lines.append(line)

    return lines if lines else [""]


def colorize_text(text, color):
    """Apply color to text"""
    if no_color:
        return text
    return f"{color}{text}{Colors.RESET}"


def colorize_cross(line):
    """Apply gold color to cross elements"""
    # Replace block characters with colored versions
    return colorize_text(line, Colors.GOLD)


def colorize_field_label(label):
    """Apply cyan color to field labels"""
    return colorize_text(label, Colors.CYAN)


def colorize_field_content(content, field):
    """Apply appropriate colors to field content"""
    if field == "[Feasts]:":
        return colorize_text(content, Colors.DEEP_RED)
    elif field == "[Saints]:":
        return colorize_text(content, Colors.BLUE)
    elif field == "[Fasting]:":
        return colorize_text(content, Colors.GREEN)
    elif field == "[Readings]:":
        return colorize_text(content, Colors.PURPLE)
    else:
        return colorize_text(content, Colors.WHITE)


def display_today():
    entry = find_today_entry()
    if not entry:
        print("No entry for today in the calendar.")
        return

    wrapped_fields = {}

    for field in FIELDS:
        text = entry.get(field, "")
        if field == "[Readings]:":
            wrapped_fields[field] = wrap_readings(text, WRAP_WIDTH)
        else:
            wrapped = textwrap.wrap(text, width=WRAP_WIDTH)
            wrapped_fields[field] = wrapped if wrapped else [""]

    cross_height = len(ORTHODOX_CROSS)
    cross_index = 0

    for field in FIELDS:
        lines = wrapped_fields[field]
        for i, line in enumerate(lines):
            # Get raw cross part
            raw_cross_part = (
                ORTHODOX_CROSS[cross_index]
                if cross_index < cross_height
                else " " * CROSS_WIDTH
            )

            # Build the raw line first (without colors)
            if i == 0:
                raw_label = field.ljust(MAX_FIELD_WIDTH)
            else:
                raw_label = " " * MAX_FIELD_WIDTH

            raw_content = line if line else ""

            # Now colorize the parts
            colored_cross = colorize_cross(raw_cross_part).ljust(
                CROSS_WIDTH + len(colorize_cross(raw_cross_part)) - len(raw_cross_part))
            colored_label = colorize_field_label(
                raw_label) if i == 0 else raw_label
            colored_content = colorize_field_content(
                raw_content, field) if raw_content else ""

            # Combine with correct spacing
            print(f"{colored_cross}{' ' * TEXT_GAP}{colored_label} {colored_content}")

            cross_index += 1

    # Print remaining cross lines if any
    for i in range(cross_index, cross_height):
        print(colorize_cross(ORTHODOX_CROSS[i]))


def list_bible_books():
    """Display all available Bible books"""
    print(colorize_text("Available Bible Books:", Colors.GOLD))
    print()

    # Group books by testament and type for better organization
    old_testament = []
    new_testament = []
    deuterocanonical = []

    # Book codes and their categories
    ot_books = ["GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA",
                "1KI", "2KI", "1CH", "2CH", "1ES", "2ES", "NEH", "EST", "JOB", "PSA", "PRO",
                "ECC", "SNG", "ISA", "JER", "LAM", "EZK", "DAN", "HOS", "JOL", "AMO",
                "OBA", "JON", "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL"]

    nt_books = ["MAT", "MRK", "LUK", "JHN", "ACT", "ROM", "1CO", "2CO", "GAL", "EPH",
                "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM", "HEB", "JAS",
                "1PE", "2PE", "1JN", "2JN", "3JN", "JUD", "REV"]

    deut_books = ["TOB", "JDT", "ESG", "WIS", "SIR", "BAR", "LJE", "1MA", "2MA", "3MA", "4MA",
                  "MAN", "P151"]

    available_codes = available_book_codes()

    for code in sorted(available_codes):
        if code in CODE_TO_NAME:
            book_name = CODE_TO_NAME[code]
            if code in ot_books:
                old_testament.append(book_name)
            elif code in nt_books:
                new_testament.append(book_name)
            elif code in deut_books:
                deuterocanonical.append(book_name)

    # Display Old Testament
    if old_testament:
        print(colorize_text("Old Testament:", Colors.DEEP_RED))
        for i, book in enumerate(old_testament, 1):
            print(f"  {colorize_text(str(i).ljust(2), Colors.CYAN)} {book}")
        print()

    # Display New Testament
    if new_testament:
        print(colorize_text("New Testament:", Colors.BLUE))
        for i, book in enumerate(new_testament, len(old_testament) + 1):
            print(f"  {colorize_text(str(i).ljust(2), Colors.CYAN)} {book}")
        print()

    # Display Deuterocanonical
    if deuterocanonical:
        print(colorize_text("Deuterocanonical:", Colors.PURPLE))
        for i, book in enumerate(deuterocanonical, len(old_testament) + len(new_testament) + 1):
            print(f"  {colorize_text(str(i).ljust(2), Colors.CYAN)} {book}")


def list_chapters(book_name):
    """Display available chapters for a specific book"""
    if not BOOK_CODES.get(book_name):
        print(colorize_text(f"Book '{book_name}' not found.", Colors.DEEP_RED))
        print(colorize_text("Use --bible to see available books.", Colors.GRAY))
        return

    try:
        data = load_book(book_name)
    except FileNotFoundError:
        print(colorize_text(
            f"Book file for {book_name} not found.", Colors.DEEP_RED))
        return

    try:
        chapters = [ch.get("chapter", 0)
                    for ch in data.get("chapters", []) if ch.get("chapter")]

        if chapters:
            print(colorize_text(
                f"Available chapters in {book_name}:", Colors.GOLD))
            print()

            # Display chapters in rows of 10
            for i in range(0, len(chapters), 10):
                row_chapters = chapters[i:i+10]
                chapter_strs = [colorize_text(
                    str(ch), Colors.CYAN) for ch in row_chapters]
                print("  " + "  ".join(chapter_strs))

            print(f"\nTotal chapters: {len(chapters)}")
            print(colorize_text(
                f"Example usage: --bible {book_name} {chapters[0]} "
                f"or --bible {book_name} {chapters[0]}:1", Colors.GRAY))
        else:
            print(colorize_text(
                f"No chapters found for {book_name}.", Colors.DEEP_RED))

    except (OSError, json.JSONDecodeError) as e:
        print(colorize_text(
            f"Error reading {book_name}: {e}", Colors.DEEP_RED))


def parse_bible_reference(args: list[str]) -> tuple[str | None, int | None, int | None, int | None]:
    """Parse Bible reference from command line arguments.

    Returns (book, chapter, start_verse, end_verse); any element may be None.
    """
    if not args:
        return None, None, None, None

    # Identify the book name: try longest prefix first (up to 4 tokens), case-insensitively
    book = None
    ref_start = 1
    for i in range(min(len(args), 4), 0, -1):
        candidate = resolve_book(' '.join(args[:i]))
        if candidate:
            book = candidate
            ref_start = i
            break
    if book is None:
        book = args[0]

    remaining = args[ref_start:]

    if not remaining:
        return book, None, None, None

    reference = ' '.join(remaining)

    range_match = re.fullmatch(r'(\d+)-(\d+)', reference)
    if book in SINGLE_CHAPTER_BOOKS and range_match:
        return book, 1, int(range_match.group(1)), int(range_match.group(2))

    if ':' in reference or '.' in reference:
        try:
            chapter, start_verse, end_verse = _parse_chapter_verse(reference)
            return book, chapter, start_verse, end_verse
        except ValueError:
            return None, None, None, None
    else:
        try:
            return book, int(remaining[-1]), None, None
        except ValueError:
            return None, None, None, None


def handle_bible_command(args):
    """Handle Bible reading commands"""
    if not args:
        list_bible_books()
        return

    # Cross-chapter range such as "Job 2:13-4:3" or "1 John 2:1-3:2"
    full_reference = ' '.join(args)
    if re.search(r'\d+[:.]\d+\s*-\s*\d+[:.]\d+$', full_reference):
        parsed = parse_reading_reference(full_reference)
        if parsed:
            print(get_bible_text(*parsed))
            return

    book, chapter, start_verse, end_verse = parse_bible_reference(args)

    if book and chapter is None:
        # List chapters for this book
        list_chapters(book)
    elif book and chapter is not None:
        # Display specific chapter or verses
        if start_verse is None:
            # Show full chapter - get the last verse
            book_code = BOOK_CODES.get(book)
            if book_code:
                last_verse = get_last_verse_in_chapter(book_code, chapter)
                if last_verse > 0:
                    text = get_bible_text(
                        book, chapter, 1, chapter, last_verse)
                else:
                    text = get_bible_text(
                        book, chapter, 1, chapter, 1)  # fallback
            else:
                text = colorize_text(
                    f"Book '{book}' not found.", Colors.DEEP_RED)
        else:
            # Show specific verses
            text = get_bible_text(
                book, chapter, start_verse, chapter, end_verse)
        print(text)
    else:
        print(colorize_text("Invalid Bible reference format.", Colors.DEEP_RED))
        print(colorize_text("Examples:", Colors.GRAY))
        print("  --bible                           # List all books")
        print("  --bible John                       # List John's chapters")
        print("  --bible John 3                     # Show John chapter 3")
        print("  --bible John 3:16                  # Show John 3:16")
        print("  --bible John 3:16-17               # Show John 3:16-17")


def get_random_verse(book_name: str | None = None) -> tuple[str | None, int | None, int | None, int | None, str | None]:
    """Get a random verse from the Bible"""
    available_codes = available_book_codes()

    if book_name:
        book_code = BOOK_CODES.get(resolve_book(book_name) or "")
        if not book_code or book_code not in available_codes:
            return None, None, None, None, f"Book '{book_name}' not found."
        available_codes = [book_code]

    if not available_codes:
        return None, None, None, None, "No Bible books available."

    book_code = random.choice(available_codes)
    book_name = CODE_TO_NAME.get(book_code, book_code)

    try:
        data = load_book(book_name)

        # Get all chapters and verses
        all_verses = []
        for chapter_data in data.get("chapters", []):
            chapter_num = chapter_data.get("chapter", 0)
            for verse_obj in chapter_data.get("verses", []):
                verse_num = verse_obj.get("verse", 0)
                all_verses.append((chapter_num, verse_num))

        if not all_verses:
            return None, None, None, None, f"No verses found in {book_name}."

        # Pick random verse
        chapter, verse = random.choice(all_verses)
        return book_name, chapter, verse, verse, None

    except (OSError, json.JSONDecodeError) as e:
        return None, None, None, None, f"Error reading {book_name}: {e}"


def handle_random_verse(book_name=None):
    """Handle random verse command"""
    book_name, chapter, verse, end_verse, error = get_random_verse(book_name)

    if error:
        print(colorize_text(error, Colors.DEEP_RED))
        return

    text = get_bible_text(book_name, chapter, verse, chapter, verse)
    print(text)


def handle_update():
    """Handle orthofetch update by running the install script"""
    try:
        # Check internet connectivity
        print(colorize_text("Checking internet connection...", Colors.CYAN))
        try:
            with socket.create_connection(("raw.githubusercontent.com", 443), timeout=5):
                pass
            print(colorize_text("✓ Internet connection available", Colors.GREEN))
        except (socket.error, socket.timeout):
            print(colorize_text("✗ No internet connection available", Colors.DEEP_RED))
            print(colorize_text(
                "Please check your connection and try again.", Colors.DEEP_RED))
            return

        # Run the update command
        print(colorize_text("Updating orthofetch...", Colors.CYAN))
        print(colorize_text(
            "This may take a few minutes as we download the latest version and data files.",
            Colors.GRAY))
        print()

        # Execute the one-liner update command
        try:
            with urllib.request.urlopen(
                "https://raw.githubusercontent.com/daomah/orthofetch/main/install.sh", timeout=30
            ) as resp:
                script_body = resp.read()
        except (urllib.error.URLError, OSError) as e:
            print(colorize_text(
                f"✗ Failed to fetch install script: {e}", Colors.DEEP_RED))
            return

        try:
            result = subprocess.run(
                ["bash"],
                input=script_body,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            print(colorize_text(
                "✗ Update timed out after 10 minutes.", Colors.DEEP_RED))
            return

        print()
        if result.returncode == 0:
            print(colorize_text("✓ Update completed successfully!", Colors.GREEN))
            print(colorize_text(
                "Orthofetch has been updated to the latest version.", Colors.GREEN))
        else:
            print(colorize_text("✗ Update failed", Colors.DEEP_RED))
            print(colorize_text(
                "Please try running the update manually or check the installation.", Colors.DEEP_RED))

    except Exception as e:  # last-resort handler for the whole update flow
        print(colorize_text(
            f"✗ Unexpected error during update: {str(e)}", Colors.DEEP_RED))


def main():
    global no_color
    parser = argparse.ArgumentParser(
        description="Orthodox Christian calendar fetch tool")
    parser.add_argument("--reading", type=int,
                        help="Display full text of specific reading number for today")
    parser.add_argument(
        "--bible", nargs="*", help="Display Bible text: --bible [BOOK] [CHAPTER[:VERSE[-VERSE]]]")
    parser.add_argument("--random-verse", nargs="*", metavar="BOOK",
                        help="Display random verse: --random-verse [BOOK]")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable colored output")
    parser.add_argument("-u", "--update", action="store_true",
                        help="Update orthofetch script and data files")

    args = parser.parse_args()

    no_color = args.no_color or bool(os.environ.get("NO_COLOR")) or not sys.stdout.isatty()

    if args.reading is not None:
        if args.reading <= 0:
            print(colorize_text("Reading number must be positive.", Colors.DEEP_RED))
            return
        display_reading(args.reading)
    elif args.bible is not None:
        handle_bible_command(args.bible)
    elif args.random_verse is not None:
        # nargs="*" gives None when the flag is absent and [] when it has no value
        handle_random_verse(' '.join(args.random_verse) or None)
    elif args.update:
        handle_update()
    else:
        display_today()


if __name__ == "__main__":
    main()
