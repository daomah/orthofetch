# orthofetch

A terminal-based Orthodox Christian calendar made in a "fetch" style for Linux, showing today's saints, feasts, fasting, and readings.

---

## Install

Run this one-liner:

```bash
/bin/sh -c "$(curl -fsSL https://raw.githubusercontent.com/libertyimp/orthofetch/main/install.sh)"
```

This will:

- Copy the `orthofetch` script to `~/.local/bin`
- Copy the calendar data to `~/.local/share/orthofetch`

Make sure `~/.local/bin` is in your `PATH` to run `orthofetch` from anywhere.

---

## Usage

Simply run:

```bash
orthofetch
```

It will display today’s Orthodox calendar entry in a neat, aligned format with the Orthodox cross.

---

## Data

Currently supports the year 2026. Future updates may include additional years or maybe things to make it prettier.

---

## License

Rogue Pact License v2
