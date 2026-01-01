#!/usr/bin/env python3
import datetime
import textwrap
import os

if os.path.exists("data/orthodox_calendar_2026.txt"):
    CALENDAR_FILE = "data/orthodox_calendar_2026.txt"
else:
    CALENDAR_FILE = os.path.expanduser("~/.local/share/orthofetch/orthodox_calendar_2026.txt")


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

TEXT_GAP = 8  # space between cross and text
WRAP_WIDTH = 60  # width of wrapped text after the gap

FIELDS = ["[Saints]:", "[Feasts]:", "[Fasting]:", "[Readings]:"]
MAX_FIELD_WIDTH = max(len(f) for f in FIELDS)
CROSS_WIDTH = max(len(line) for line in ORTHODOX_CROSS)

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

def display_today():
    today = datetime.date.today()
    calendar = parse_calendar(CALENDAR_FILE)
    today_str = today.strftime("📅 %A, %B %-d, %Y")
    
    entry = None
    for key in calendar.keys():
        if key.startswith(today_str):
            entry = calendar[key]
            break

    if not entry:
        print("No entry for today in the calendar.")
        return

    # wrap each field
    wrapped_fields = {}
    for field in FIELDS:
        text = entry.get(field, "")
        wrapped_lines = textwrap.wrap(text, width=WRAP_WIDTH)
        wrapped_fields[field] = wrapped_lines if wrapped_lines else [""]

    # prepare printing
    cross_height = len(ORTHODOX_CROSS)
    max_lines = max(cross_height, sum(len(lines) for lines in wrapped_fields.values()))
    cross_index = 0

    for field in FIELDS:
        lines = wrapped_fields[field]
        for i, line in enumerate(lines):
            cross_part = ORTHODOX_CROSS[cross_index] if cross_index < cross_height else " " * CROSS_WIDTH
            label = field.ljust(MAX_FIELD_WIDTH) if i == 0 else " " * MAX_FIELD_WIDTH
            print(f"{cross_part.ljust(CROSS_WIDTH)}{' ' * TEXT_GAP}{label} {line}")
            cross_index += 1

    # remaining cross lines if any
    for i in range(cross_index, cross_height):
        print(ORTHODOX_CROSS[i])

if __name__ == "__main__":
    display_today()
