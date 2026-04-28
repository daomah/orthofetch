#!/usr/bin/env python3
import datetime
import textwrap
import os
import argparse
import re
import sys
import subprocess
import socket

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

# Locate calendar file
if os.path.exists("data/orthodox_calendar_2026.txt"):
    CALENDAR_FILE = "data/orthodox_calendar_2026.txt"
    BIBLE_DIR = "data/bible"
else:
    CALENDAR_FILE = os.path.expanduser(
        "~/.local/share/orthofetch/orthodox_calendar_2026.txt"
    )
    BIBLE_DIR = os.path.expanduser("~/.local/share/orthofetch/bible")

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
    "Wisdom of Solomon": "WIS", "Sirach": "SIR", "Baruch": "BAR", "1 Maccabees": "1MA", "2 Maccabees": "2MA", "3 Maccabees": "3MA", "4 Maccabees": "4MA", "Tobit": "TOB", "Judith": "JDT", "Esther (Greek)": "ESG",
    "Psalm 151": "P151", "Prayer of Manasseh": "MAN", "1 Ezra": "1ES", "2 Ezra": "2ES"
}

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


def parse_reading_reference(reference):
    """Parse a reading reference like 'Genesis 3:1-8', 'John 10:9', 'Exodus 15.22-16.1', '3[1] Kings 2.6-14', 'Numbers 8', 'Exodus 12, 13'
    
    Returns:
        None if parsing fails
        Tuple of (book, start_chapter, start_verse, end_chapter, end_verse)
        Always returns 5 elements for consistency
    """
    # Handle special case for Wisdom of Solomon
    if reference.startswith('Wisdom ') and not reference.startswith('Wisdom of '):
        reference = 'Wisdom of Solomon' + reference[6:]
    
    # Handle special format like "3[1] Kings 2.6-14" - extract the second number in brackets
    reference = re.sub(r'(\d+)\[(\d+)\]\s+Kings', r'\2 Kings', reference)
    
    # Convert dots to colons for consistency (but keep original for parsing cross-chapter ranges)
    reference_clean = reference.replace('.', ':')
    
    # Check for cross-chapter pattern: Book Chapter:Verse-Chapter:Verse
    cross_chapter_pattern = r"([0-9A-Za-z\s]+)\s+(\d+)[:](\d+)[-:](\d+)[:](\d+)$"
    cross_match = re.match(cross_chapter_pattern, reference_clean.strip())
    
    if cross_match:
        book = cross_match.group(1).strip()
        start_chapter = int(cross_match.group(2))
        start_verse = int(cross_match.group(3))
        end_chapter = int(cross_match.group(4))
        end_verse = int(cross_match.group(5))
        
        return book, start_chapter, start_verse, end_chapter, end_verse
    
    # Pattern to match: Book Chapter:Verse-Verse or Book Chapter:Verse (single chapter)
    single_chapter_pattern = r"([0-9A-Za-z\s]+)\s+(\d+)[:](\d+)(?:[-:]?(\d+))?"
    match = re.match(single_chapter_pattern, reference_clean.strip())
    
    if match:
        book = match.group(1).strip()
        chapter = int(match.group(2))
        start_verse = int(match.group(3))
        end_verse = int(match.group(4)) if match.group(4) else start_verse
        
        # Return in 5-tuple format for consistency (start_chapter = end_chapter)
        return book, chapter, start_verse, chapter, end_verse
    
    # Pattern to match: Book Chapter (no verses)
    chapter_only_pattern = r"([0-9A-Za-z\s]+)\s+(\d+)$"
    chapter_match = re.match(chapter_only_pattern, reference.strip())
    
    if chapter_match:
        book = chapter_match.group(1).strip()
        chapter = int(chapter_match.group(2))
        
        # Return chapter-only reference - verse range will be determined later
        return book, chapter, None, chapter, None
    
    # Pattern to match: Book Chapter, Chapter (comma-separated chapters)
    comma_chapter_pattern = r"([0-9A-Za-z\s]+)\s+(\d+),\s*(\d+)$"
    comma_chapter_match = re.match(comma_chapter_pattern, reference.strip())
    
    if comma_chapter_match:
        book = comma_chapter_match.group(1).strip()
        start_chapter = int(comma_chapter_match.group(2))
        end_chapter = int(comma_chapter_match.group(3))
        
        # Return cross-chapter reference with no verses
        return book, start_chapter, None, end_chapter, None
    
    return None


def get_last_verse_in_chapter(book_code, chapter):
    """Get the last verse number in a chapter"""
    import json
    
    # Map book code to JSON filename (lowercase)
    code_to_name = {}
    for name, code in BOOK_CODES.items():
        code_to_name[code] = name.lower().replace(' ', '_').replace('of_solomon', '')
    
    # Handle special cases for book names
    json_filename = code_to_name.get(book_code, book_code.lower())
    if json_filename.startswith('1_') or json_filename.startswith('2_') or json_filename.startswith('3_'):
        json_filename = json_filename.replace('_', '')
    elif 'wisdom' in json_filename:
        json_filename = 'wisdom'
    elif 'song' in json_filename:
        json_filename = 'songs'
    elif 'esther_(greek)' in json_filename:
        json_filename = 'esther_greek'
    
    json_file = os.path.join(BIBLE_DIR, f"{json_filename}.json")
    if not os.path.exists(json_file):
        return 0
    
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Find the requested chapter
        for chapter_data in data.get("chapters", []):
            if chapter_data.get("chapter") == chapter:
                verses = chapter_data.get("verses", [])
                if verses:
                    return verses[-1].get("verse", 0)
        
        return 0
    except Exception:
        return 0


def get_bible_text(book, start_chapter, start_verse, end_chapter=None, end_verse=None):
    """Retrieve bible text for the specified reference. Supports cross-chapter ranges and chapter-only references."""
    import json
    
    # Handle backward compatibility: if end_chapter is None, assume single chapter range
    if end_chapter is None:
        end_chapter = start_chapter
        if end_verse is None:
            end_verse = start_verse
    
    # Handle chapter-only references - get entire chapter(s)
    if start_verse is None:
        start_verse = 1
    if end_verse is None:
        # Get last verse of the end chapter
        book_code = BOOK_CODES.get(book)
        if book_code:
            end_verse = get_last_verse_in_chapter(book_code, end_chapter)
        else:
            end_verse = 1
    
    book_code = BOOK_CODES.get(book)
    if not book_code:
        return f"Book '{book}' not found."
    
    # Map book code to JSON filename (lowercase)
    code_to_name = {}
    for name, code in BOOK_CODES.items():
        code_to_name[code] = name.lower().replace(' ', '_').replace('of_solomon', '')
    
    # Handle special cases for book names
    json_filename = code_to_name.get(book_code, book_code.lower())
    if json_filename.startswith('1_') or json_filename.startswith('2_') or json_filename.startswith('3_'):
        json_filename = json_filename.replace('_', '')
    elif 'wisdom' in json_filename:
        json_filename = 'wisdom'
    elif 'song' in json_filename:
        json_filename = 'songs'
    elif 'esther_(greek)' in json_filename:
        json_filename = 'esther_greek'
    
    json_file = os.path.join(BIBLE_DIR, f"{json_filename}.json")
    if not os.path.exists(json_file):
        return f"Book {book} not found."
    
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        all_chapters = {ch.get("chapter"): ch for ch in data.get("chapters", [])}
        result_lines = []
        
        # Handle cross-chapter range
        if end_chapter > start_chapter:
            # First chapter: from start_verse to end of chapter
            first_chapter = all_chapters.get(start_chapter)
            if first_chapter:
                for verse_obj in first_chapter.get("verses", []):
                    verse_num = verse_obj.get("verse", 0)
                    if verse_num >= start_verse:
                        verse_text = verse_obj.get("text", "")
                        result_lines.append(f"{verse_num} {verse_text}")
            
            # Middle chapters: all verses
            for chapter_num in range(start_chapter + 1, end_chapter):
                middle_chapter = all_chapters.get(chapter_num)
                if middle_chapter:
                    for verse_obj in middle_chapter.get("verses", []):
                        verse_num = verse_obj.get("verse", 0)
                        verse_text = verse_obj.get("text", "")
                        result_lines.append(f"{verse_num} {verse_text}")
            
            # Last chapter: from verse 1 to end_verse
            last_chapter = all_chapters.get(end_chapter)
            if last_chapter:
                for verse_obj in last_chapter.get("verses", []):
                    verse_num = verse_obj.get("verse", 0)
                    if verse_num <= end_verse:
                        verse_text = verse_obj.get("text", "")
                        result_lines.append(f"{verse_num} {verse_text}")
        else:
            # Single chapter range (original logic)
            chapter_data = all_chapters.get(start_chapter)
            if not chapter_data:
                return f"Chapter {start_chapter} of {book} not found."
            
            verses = chapter_data.get("verses", [])
            for verse_obj in verses:
                verse_num = verse_obj.get("verse", 0)
                if start_verse <= verse_num <= end_verse:
                    verse_text = verse_obj.get("text", "")
                    result_lines.append(f"{verse_num} {verse_text}")
        
        if result_lines:
            # Create appropriate header
            if end_chapter > start_chapter:
                # Cross-chapter range
                if start_verse == 1 and end_verse == get_last_verse_in_chapter(BOOK_CODES.get(book), end_chapter):
                    # Full chapters
                    header = f"{book} {start_chapter}-{end_chapter}"
                else:
                    # Partial chapters
                    header = f"{book} {start_chapter}:{start_verse}-{end_chapter}:{end_verse}"
            else:
                # Single chapter
                if start_verse == 1 and end_verse == get_last_verse_in_chapter(BOOK_CODES.get(book), start_chapter):
                    # Full chapter
                    header = f"{book} {start_chapter}"
                else:
                    # Partial chapter
                    header = f"{book} {start_chapter}:{start_verse}"
                    if end_verse != start_verse:
                        header += f"-{end_verse}"
            
            # Colorize the header
            colored_header = colorize_text(header, Colors.GOLD)
            colored_verses = []
            for verse in result_lines:
                # Split verse number from text
                if verse and verse[0].isdigit():
                    space_pos = verse.find(' ')
                    if space_pos > 0:
                        verse_num = verse[:space_pos]
                        verse_text = verse[space_pos+1:]
                        colored_verses.append(
                            colorize_text(verse_num, Colors.CYAN) + " " + 
                            colorize_text(verse_text, Colors.WHITE)
                        )
                    else:
                        colored_verses.append(colorize_text(verse, Colors.WHITE))
                else:
                    colored_verses.append(colorize_text(verse, Colors.WHITE))
            
            return f"\n{colored_header}\n" + "\n".join(colored_verses)
        else:
            if end_chapter > start_chapter:
                return colorize_text(f"Verses {start_chapter}:{start_verse}-{end_chapter}:{end_verse} not found in {book}.", Colors.GRAY)
            else:
                return colorize_text(f"Verses {start_verse}-{end_verse} not found in {book} {start_chapter}.", Colors.GRAY)
            
    except Exception as e:
        if end_chapter > start_chapter:
            return f"Error reading {book} {start_chapter}:{start_verse}-{end_chapter}:{end_verse}: {e}"
        else:
            return f"Error reading {book} {start_chapter}:{start_verse}-{end_verse}: {e}"


def display_reading(reading_number):
    """Display the full text of a specific reading for today"""
    today = datetime.date.today()
    calendar = parse_calendar(CALENDAR_FILE)
    today_str = f"📅 {today:%A, %B} {today.day}, {today.year}"

    entry = None
    for key in calendar:
        if key.startswith(today_str):
            entry = calendar[key]
            break

    if not entry:
        print(colorize_text("No entry for today in the calendar.", Colors.GRAY))
        return

    readings_text = entry.get("[Readings]:", "")
    if not readings_text:
        print(colorize_text("No readings for today.", Colors.GRAY))
        return

    # Split readings by " • " first
    readings = [r.strip() for r in readings_text.split(" • ") if r.strip()]
    
    # Filter out "Composite X - " prefix and handle complex formats
    clean_readings = []
    for reading in readings:
        if reading.startswith("Composite"):
            # Remove "Composite X - " prefix
            clean_reading = re.sub(r'^Composite \d+ -\s*', '', reading)
            # Handle cases with semicolons and multiple readings
            if ';' in clean_reading:
                # Split by semicolon first
                semicolon_parts = [p.strip() for p in clean_reading.split(';')]
                for part in semicolon_parts:
                    if part:
                        # Then split by • within each semicolon part
                        sub_parts = [r.strip() for r in part.split(" • ") if r.strip()]
                        clean_readings.extend(sub_parts)
            else:
                # Split by • as before
                sub_parts = [r.strip() for r in clean_reading.split(" • ") if r.strip()]
                clean_readings.extend(sub_parts)
        else:
            clean_readings.append(reading)
    
    # Filter out any empty entries
    clean_readings = [r for r in clean_readings if r and not r.isdigit()]

    try:
        reading_idx = int(reading_number) - 1
        if reading_idx < 0 or reading_idx >= len(clean_readings):
            print(colorize_text(f"Reading number {reading_number} not found. There are {len(clean_readings)} readings today.", Colors.DEEP_RED))
            print(colorize_text("Available readings:", Colors.CYAN))
            for i, reading in enumerate(clean_readings, 1):
                print(f"  {colorize_text(str(i), Colors.GOLD)}. {colorize_text(reading, Colors.PURPLE)}")
            return

        reading_ref = clean_readings[reading_idx]
        
        # Handle multiple verse ranges separated by commas
        if ',' in reading_ref:
            # Try to parse as single reference first (for cases like "Exodus 12, 13")
            single_parsed = parse_reading_reference(reading_ref)
            if single_parsed and single_parsed[2] is None and single_parsed[4] is None:
                # This is a comma-separated chapter reference (like "Exodus 12, 13")
                book, start_chapter, start_verse, end_chapter, end_verse = single_parsed
                text = get_bible_text(book, start_chapter, start_verse, end_chapter, end_verse)
                print(text)
                return
            
            # If single parsing failed, try multi-part parsing
            parts = [p.strip() for p in reading_ref.split(',')]
            parsed_references = []
            book = None
            
            for part in parts:
                if ':' in part or '.' in part:
                    # Check if this looks like a full reference (has book name) or just chapter.verses
                    # A full book reference like "1 Peter 1.1-2" will have space(s) after the book name
                    # A simple chapter.verse reference like "3.4-7" or "3:4-7" will not have spaces before the first . or :
                    has_book_name = re.search(r'\d+[A-Za-z\s]+\d+[.:]', part) is not None
                    if part[0].isdigit() and ('.' in part or ':' in part) and not has_book_name:
                        # This looks like "3.4-7" (chapter.verses without book)
                        if parsed_references:
                            # Use book from first reference
                            current_book = parsed_references[0][0]
                            try:
                                if '.' in part:
                                    chapter_part, verse_part = part.split('.')
                                    chapter = int(chapter_part)
                                    if '-' in verse_part:
                                        start_verse, end_verse = verse_part.split('-')
                                        parsed_references.append((current_book, chapter, int(start_verse), chapter, int(end_verse)))
                                    else:
                                        parsed_references.append((current_book, chapter, int(verse_part), chapter, int(verse_part)))
                                else:
                                    # Handle "3:4-7" format
                                    chapter_part, verse_part = part.split(':')
                                    chapter = int(chapter_part)
                                    if '-' in verse_part:
                                        start_verse, end_verse = verse_part.split('-')
                                        parsed_references.append((current_book, chapter, int(start_verse), chapter, int(end_verse)))
                                    else:
                                        parsed_references.append((current_book, chapter, int(verse_part), chapter, int(verse_part)))
                            except ValueError:
                                print(colorize_text(f"Could not parse chapter.verse reference: {part}", Colors.DEEP_RED))
                                return
                        else:
                            print(colorize_text(f"Could not determine book for reference: {part}", Colors.DEEP_RED))
                            return
                    else:
                        # Full reference with book name
                        range_parsed = parse_reading_reference(part)
                        if range_parsed:
                            current_book, start_chapter, start_verse, end_chapter, end_verse = range_parsed
                            if book is None:
                                book = current_book
                            parsed_references.append((current_book, start_chapter, start_verse, end_chapter, end_verse))
                        else:
                            print(colorize_text(f"Could not parse reading reference: {part}", Colors.DEEP_RED))
                            return
                else:
                    # Just verse range - use book and chapter from first parsed part
                    if parsed_references:
                        current_book, start_chapter, _, _, _ = parsed_references[0]
                        if '-' in part:
                            try:
                                start_verse, end_verse = part.split('-')
                                parsed_references.append((current_book, start_chapter, int(start_verse), start_chapter, int(end_verse)))
                            except ValueError:
                                print(colorize_text(f"Could not parse verse range: {part}", Colors.DEEP_RED))
                                return
                        else:
                            try:
                                parsed_references.append((current_book, start_chapter, int(part), start_chapter, int(part)))
                            except ValueError:
                                print(colorize_text(f"Could not parse verse: {part}", Colors.DEEP_RED))
                                return
                    else:
                        print(colorize_text(f"Could not determine book for verse range: {part}", Colors.DEEP_RED))
                        return
            
            if parsed_references:
                # Check if all references are from the same book
                all_same_book = all(ref[0] == parsed_references[0][0] for ref in parsed_references)
                
                if all_same_book:
                    # All references from same book - print each separately (they might be different chapters)
                    for ref_book, start_chapter, start_verse, end_chapter, end_verse in parsed_references:
                        text = get_bible_text(ref_book, start_chapter, start_verse, end_chapter, end_verse)
                        print(text)
                else:
                    # Different books - print each separately
                    for ref_book, start_chapter, start_verse, end_chapter, end_verse in parsed_references:
                        text = get_bible_text(ref_book, start_chapter, start_verse, end_chapter, end_verse)
                        print(text)
        else:
            # Single range - existing logic
            parsed = parse_reading_reference(reading_ref)
            
            if parsed:
                book, start_chapter, start_verse, end_chapter, end_verse = parsed
                text = get_bible_text(book, start_chapter, start_verse, end_chapter, end_verse)
                print(text)
            else:
                print(colorize_text(f"Could not parse reading reference: {reading_ref}", Colors.DEEP_RED))
            
    except ValueError:
        print("Please provide a valid reading number (e.g., --reading 1)")


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
    # Parse the readings the same way as display_reading to get clean list
    readings = [r.strip() for r in text.split(" • ") if r.strip()]
    clean_readings = []
    
    for reading in readings:
        if reading.startswith("Composite"):
            # Remove "Composite X - " prefix
            clean_reading = re.sub(r'^Composite \d+ -\s*', '', reading)
            # Handle cases with semicolons and multiple readings
            if ';' in clean_reading:
                # Split by semicolon first
                semicolon_parts = [p.strip() for p in clean_reading.split(';')]
                for part in semicolon_parts:
                    if part:
                        # Then split by • within each semicolon part
                        sub_parts = [r.strip() for r in part.split(" • ") if r.strip()]
                        clean_readings.extend(sub_parts)
            else:
                # Split by • as before
                sub_parts = [r.strip() for r in clean_reading.split(" • ") if r.strip()]
                clean_readings.extend(sub_parts)
        else:
            clean_readings.append(reading)
    
    # Clean up Kings book format for display
    for i in range(len(clean_readings)):
        # Convert "3[1] Kings" to "1 Kings" for display
        clean_readings[i] = re.sub(r'\d+\[(\d+)\]\s+Kings', r'\1 Kings', clean_readings[i])
    
    # Filter out any empty entries
    clean_readings = [r for r in clean_readings if r and not r.isdigit()]
    
    lines = []
    
    for i, reading in enumerate(clean_readings, 1):
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
    today = datetime.date.today()
    calendar = parse_calendar(CALENDAR_FILE)
    today_str = f"📅 {today:%A, %B} {today.day}, {today.year}"

    entry = None
    for key in calendar:
        if key.startswith(today_str):
            entry = calendar[key]
            break

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
            raw_line = f"{raw_cross_part.ljust(CROSS_WIDTH)}{' ' * TEXT_GAP}{raw_label} {raw_content}"
            
            # Now colorize the parts
            colored_cross = colorize_cross(raw_cross_part).ljust(CROSS_WIDTH + len(colorize_cross(raw_cross_part)) - len(raw_cross_part))
            colored_label = colorize_field_label(raw_label) if i == 0 else raw_label
            colored_content = colorize_field_content(raw_content, field) if raw_content else ""
            
            # Combine with correct spacing
            print(f"{colored_cross}{' ' * TEXT_GAP}{colored_label} {colored_content}")

            cross_index += 1

    # Print remaining cross lines if any
    for i in range(cross_index, cross_height):
        print(colorize_cross(ORTHODOX_CROSS[i]))


def list_bible_books():
    """Display all available Bible books"""
    import json
    
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
    
    deut_books = ["TOB", "JDT", "ESG", "WIS", "SIR", "BAR", "1MA", "2MA", "3MA", "4MA",
                  "MAN", "P151"]
    
    # Create reverse lookup from BOOK_CODES
    code_to_name = {}
    for name, code in BOOK_CODES.items():
        code_to_name[code] = name
    
    # Create filename to book code mapping
    filename_to_code = {}
    for name, code in BOOK_CODES.items():
        # Convert book name to expected JSON filename
        filename = name.lower().replace(' ', '_').replace('of_solomon', '')
        if filename.startswith('1_') or filename.startswith('2_') or filename.startswith('3_'):
            filename = filename.replace('_', '')
        elif 'wisdom' in filename:
            filename = 'wisdom'
        elif 'song' in filename:
            filename = 'songs'
        elif 'esther_(greek)' in filename:
            filename = 'esther_greek'
        filename_to_code[filename] = code
    
    # Check which books are actually available from JSON files
    available_codes = []
    if os.path.exists(BIBLE_DIR):
        for file in os.listdir(BIBLE_DIR):
            if file.endswith('.json'):
                filename = file[:-5]  # Remove .json extension
                if filename in filename_to_code:
                    available_codes.append(filename_to_code[filename])
    
    # Organize books by category
    for code in sorted(available_codes):
        if code in code_to_name:
            book_name = code_to_name[code]
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
    import json
    
    book_code = BOOK_CODES.get(book_name)
    if not book_code:
        print(colorize_text(f"Book '{book_name}' not found.", Colors.DEEP_RED))
        print(colorize_text("Use --bible to see available books.", Colors.GRAY))
        return
    
    # Map book code to JSON filename (lowercase)
    code_to_name = {}
    for name, code in BOOK_CODES.items():
        code_to_name[code] = name.lower().replace(' ', '_').replace('of_solomon', '')
    
    # Handle special cases for book names
    json_filename = code_to_name.get(book_code, book_code.lower())
    if json_filename.startswith('1_') or json_filename.startswith('2_') or json_filename.startswith('3_'):
        json_filename = json_filename.replace('_', '')
    elif 'wisdom' in json_filename:
        json_filename = 'wisdom'
    elif 'song' in json_filename:
        json_filename = 'songs'
    elif 'esther_(greek)' in json_filename:
        json_filename = 'esther_greek'
    
    json_file = os.path.join(BIBLE_DIR, f"{json_filename}.json")
    if not os.path.exists(json_file):
        print(colorize_text(f"Book file for {book_name} not found.", Colors.DEEP_RED))
        return
    
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        chapters = [ch.get("chapter", 0) for ch in data.get("chapters", []) if ch.get("chapter")]
        
        if chapters:
            print(colorize_text(f"Available chapters in {book_name}:", Colors.GOLD))
            print()
            
            # Display chapters in rows of 10
            for i in range(0, len(chapters), 10):
                row_chapters = chapters[i:i+10]
                chapter_strs = [colorize_text(str(ch), Colors.CYAN) for ch in row_chapters]
                print("  " + "  ".join(chapter_strs))
            
            print(f"\nTotal chapters: {len(chapters)}")
            print(colorize_text(f"Example usage: --bible {book_name} {chapters[0]} or --bible {book_name} {chapters[0]}:1", Colors.GRAY))
        else:
            print(colorize_text(f"No chapters found for {book_name}.", Colors.DEEP_RED))
            
    except Exception as e:
        print(colorize_text(f"Error reading {book_name}: {e}", Colors.DEEP_RED))


def parse_bible_reference(args):
    """Parse Bible reference from command line arguments"""
    if not args:
        return None, None, None, None
    
    if len(args) == 1:
        # Just book name
        return args[0], None, None, None
    elif len(args) == 2:
        # Book and chapter OR Book and chapter:verse (handle multi-word books)
        potential_book = args[0]
        if len(args) >= 2 and f"{args[0]} {args[1]}" in BOOK_CODES:
            # Multi-word book like "1 Kings"
            potential_book = f"{args[0]} {args[1]}"
            book = potential_book
            if len(args) == 2:
                # Just book name
                return book, None, None, None
            else:
                # Book and chapter:verse
                remaining_args = args[2:] if len(args) > 2 else []
                reference_str = ' '.join(remaining_args) if remaining_args else args[2] if len(args) > 2 else ''
                if ':' in reference_str:
                    # Format: "1 Kings 3:1-5"
                    try:
                        chapter_part, verse_part = reference_str.split(':')
                        chapter = int(chapter_part)
                        if '-' in verse_part:
                            # Range: 3:1-5
                            start_verse, end_verse = verse_part.split('-')
                            verse = int(start_verse)
                            end_verse = int(end_verse)
                            return book, chapter, verse, end_verse
                        else:
                            # Single verse: 3:1
                            verse = int(verse_part)
                            return book, chapter, verse, verse
                    except ValueError:
                        return None, None, None, None
                elif '.' in reference_str:
                    # Format: "1 Kings 3.1-5" - convert dot to colon
                    reference_fixed = reference_str.replace('.', ':')
                    try:
                        chapter_part, verse_part = reference_fixed.split(':')
                        chapter = int(chapter_part)
                        if '-' in verse_part:
                            # Range: 3:1-5
                            start_verse, end_verse = verse_part.split('-')
                            verse = int(start_verse)
                            end_verse = int(end_verse)
                            return book, chapter, verse, end_verse
                        else:
                            # Single verse: 3:1
                            verse = int(verse_part)
                            return book, chapter, verse, verse
                    except ValueError:
                        return None, None, None, None
                else:
                    # Book and chapter only (e.g., "1 Kings 3")
                    try:
                        chapter = int(remaining_args[-1]) if remaining_args else None
                        return book, chapter, None, None
                    except ValueError:
                        return None, None, None, None
        elif ':' in args[1]:
            # Format: John 3:16
            try:
                chapter_part, verse_part = args[1].split(':')
                chapter = int(chapter_part)
                if '-' in verse_part:
                    # Range: 3:16-17
                    start_verse, end_verse = verse_part.split('-')
                    verse = int(start_verse)
                    end_verse = int(end_verse)
                    return args[0], chapter, verse, end_verse
                else:
                    # Single verse: 3:16
                    verse = int(verse_part)
                    return args[0], chapter, verse, verse
            except ValueError:
                return None, None, None, None
        else:
            # Book and chapter only
            try:
                chapter = int(args[1])
                return args[0], chapter, None, None
            except ValueError:
                return None, None, None, None
    elif len(args) >= 3:
        # Book with spaces and chapter:verse (e.g., "1 Kings 3.1-5" or "1 Kings 3:1-5")
        # Find book name by combining arguments until we find a valid book
        book_found = None
        ref_start_idx = None
        
        # Try different combinations to find valid book
        for i in range(min(len(args), 3), 0, -1):  # Start from longer combos, go down
            potential_book = ' '.join(args[:i])
            if potential_book in BOOK_CODES:  # Check in keys, not values
                book_found = potential_book
                ref_start_idx = i
                break
        
        if book_found:
            book = book_found
            remaining_args = args[ref_start_idx:]
            reference = ' '.join(remaining_args)
        else:
            # Fallback: treat first arg as book
            book = args[0]
            remaining_args = args[1:]
            reference = ' '.join(remaining_args)
        
        # Handle both dot and colon formats
        if ':' in reference:
            # Format: "1 Kings 3:1-5"
            try:
                chapter_part, verse_part = reference.split(':')
                chapter = int(chapter_part)
                if '-' in verse_part:
                    # Range: 3:1-5
                    start_verse, end_verse = verse_part.split('-')
                    verse = int(start_verse)
                    end_verse = int(end_verse)
                    return book, chapter, verse, end_verse
                else:
                    # Single verse: 3:1
                    verse = int(verse_part)
                    return book, chapter, verse, verse
            except ValueError:
                return None, None, None, None
        elif '.' in reference:
            # Format: "1 Kings 3.1-5" - convert dot to colon
            reference = reference.replace('.', ':')
            try:
                chapter_part, verse_part = reference.split(':')
                chapter = int(chapter_part)
                if '-' in verse_part:
                    # Range: 3:1-5
                    start_verse, end_verse = verse_part.split('-')
                    verse = int(start_verse)
                    end_verse = int(end_verse)
                    return book, chapter, verse, end_verse
                else:
                    # Single verse: 3:1
                    verse = int(verse_part)
                    return book, chapter, verse, verse
            except ValueError:
                return None, None, None, None
        else:
            # Book and chapter only (e.g., "1 Kings 3")
            try:
                chapter = int(remaining_args[-1])  # Last argument should be chapter
                return book, chapter, None, None
            except ValueError:
                return None, None, None, None

    return None, None, None, None


def handle_bible_command(args):
    """Handle Bible reading commands"""
    if not args:
        list_bible_books()
        return
    
    # Check for cross-chapter range format like "Job 2:13-4:3"
    if len(args) >= 2 and '-' in args[1] and ':' in args[1]:
        dash_pos = args[1].find('-')
        if dash_pos > 0 and ':' in args[1][dash_pos+1:]:
            # This looks like cross-chapter range
            full_reference = ' '.join(args)
            parsed = parse_reading_reference(full_reference)
            if parsed:
                book, start_chapter, start_verse, end_chapter, end_verse = parsed
                text = get_bible_text(book, start_chapter, start_verse, end_chapter, end_verse)
                print(text)
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
                    text = get_bible_text(book, chapter, 1, chapter, last_verse)
                else:
                    text = get_bible_text(book, chapter, 1, chapter, 1)  # fallback
            else:
                text = colorize_text(f"Book '{book}' not found.", Colors.DEEP_RED)
        else:
            # Show specific verses
            text = get_bible_text(book, chapter, start_verse, chapter, end_verse)
        print(text)
    else:
        print(colorize_text("Invalid Bible reference format.", Colors.DEEP_RED))
        print(colorize_text("Examples:", Colors.GRAY))
        print("  --bible                           # List all books")
        print("  --bible John                       # List John's chapters")
        print("  --bible John 3                     # Show John chapter 3")
        print("  --bible John 3:16                  # Show John 3:16")
        print("  --bible John 3:16-17               # Show John 3:16-17")


def get_random_verse(book_name=None):
    """Get a random verse from the Bible"""
    import random
    import json
    
    # Create filename to book code mapping
    filename_to_code = {}
    code_to_name = {}
    for name, code in BOOK_CODES.items():
        code_to_name[code] = name
        # Convert book name to expected JSON filename
        filename = name.lower().replace(' ', '_').replace('of_solomon', '')
        if filename.startswith('1_') or filename.startswith('2_') or filename.startswith('3_'):
            filename = filename.replace('_', '')
        elif 'wisdom' in filename:
            filename = 'wisdom'
        elif 'song' in filename:
            filename = 'songs'
        elif 'esther_(greek)' in filename:
            filename = 'esther_greek'
        filename_to_code[filename] = code
    
    # Get available books from JSON files
    available_codes = []
    if os.path.exists(BIBLE_DIR):
        for file in os.listdir(BIBLE_DIR):
            if file.endswith('.json'):
                filename = file[:-5]  # Remove .json extension
                if filename in filename_to_code:
                    available_codes.append(filename_to_code[filename])
    
    # Filter by specific book if requested
    if book_name:
        book_code = BOOK_CODES.get(book_name)
        if not book_code or book_code not in available_codes:
            return None, None, None, None, f"Book '{book_name}' not found."
        available_codes = [book_code]
    
    if not available_codes:
        return None, None, None, None, "No Bible books available."
    
    # Pick random book
    book_code = random.choice(available_codes)
    book_name = code_to_name.get(book_code, book_code)
    
    # Get JSON filename
    json_filename = None
    for filename, code in filename_to_code.items():
        if code == book_code:
            json_filename = filename
            break
    
    if not json_filename:
        return None, None, None, None, f"Could not find JSON file for {book_name}."
    
    json_file = os.path.join(BIBLE_DIR, f"{json_filename}.json")
    
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
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
        
    except Exception as e:
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
            socket.create_connection(("raw.githubusercontent.com", 443), timeout=5)
            print(colorize_text("✓ Internet connection available", Colors.GREEN))
        except (socket.error, socket.timeout):
            print(colorize_text("✗ No internet connection available", Colors.DEEP_RED))
            print(colorize_text("Please check your connection and try again.", Colors.DEEP_RED))
            return
        
        # Run the update command
        print(colorize_text("Updating orthofetch...", Colors.CYAN))
        print(colorize_text("This may take a few minutes as we download the latest version and data files.", Colors.GRAY))
        print()
        
        # Execute the one-liner update command
        try:
            import urllib.request
            with urllib.request.urlopen(
                "https://raw.githubusercontent.com/daomah/orthofetch/main/install.sh", timeout=30
            ) as resp:
                script_body = resp.read()
        except Exception as e:
            print(colorize_text(f"✗ Failed to fetch install script: {e}", Colors.DEEP_RED))
            return

        try:
            result = subprocess.run(
                ["sh"],
                input=script_body,
                capture_output=True,
                timeout=600,
            )
        except subprocess.TimeoutExpired:
            print(colorize_text("✗ Update timed out after 10 minutes.", Colors.DEEP_RED))
            return

        if result.returncode == 0:
            print()
            print(colorize_text("✓ Update completed successfully!", Colors.GREEN))
            print(colorize_text("Orthofetch has been updated to the latest version.", Colors.GREEN))
        else:
            print()
            print(colorize_text("✗ Update failed", Colors.DEEP_RED))
            if result.stderr:
                print(colorize_text(f"Error: {result.stderr.decode(errors='replace').strip()}", Colors.DEEP_RED))
            print(colorize_text("Please try running the update manually or check the installation.", Colors.DEEP_RED))

    except Exception as e:
        print(colorize_text(f"✗ Unexpected error during update: {str(e)}", Colors.DEEP_RED))


def main():
    global no_color
    parser = argparse.ArgumentParser(description="Orthodox Christian calendar fetch tool")
    parser.add_argument("--reading", type=int, help="Display full text of specific reading number for today")
    parser.add_argument("--bible", nargs="*", help="Display Bible text: --bible [BOOK] [CHAPTER[:VERSE[-VERSE]]]")
    parser.add_argument("--random-verse", nargs="?", help="Display random verse: --random-verse [BOOK]")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("-u", "--update", action="store_true", help="Update orthofetch script and data files")
    
    args = parser.parse_args()
    
    no_color = args.no_color
    
    # Check which arguments were actually provided
    provided_args = [arg for arg in sys.argv if arg.startswith('--')]
    
    if args.reading is not None:
        if args.reading <= 0:
            print(colorize_text("Reading number must be positive.", Colors.DEEP_RED))
            return
        display_reading(args.reading)
    elif '--bible' in provided_args:
        handle_bible_command(args.bible)
    elif '--random-verse' in provided_args:
        handle_random_verse(args.random_verse)
    elif '--update' in provided_args or '-u' in sys.argv:
        handle_update()
    else:
        display_today()


if __name__ == "__main__":
    main()

