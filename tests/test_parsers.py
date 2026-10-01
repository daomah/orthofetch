#!/usr/bin/env python3
"""Tests for parse_reading_reference, parse_bible_reference, and bible_filename."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from orthofetch import (  # noqa: E402
    bible_filename, clean_readings, normalize_kings, normalize_reference, parse_bible_reference,
    parse_multi_reference, parse_reading_reference, resolve_book,
)


class TestBibleFilename(unittest.TestCase):
    def test_simple_name(self):
        self.assertEqual(bible_filename("Genesis"), "genesis")

    def test_numbered_book(self):
        self.assertEqual(bible_filename("1 Kings"), "1kings")
        self.assertEqual(bible_filename("2 Samuel"), "2samuel")
        self.assertEqual(bible_filename("3 John"), "3john")

    def test_wisdom_of_solomon(self):
        self.assertEqual(bible_filename("Wisdom of Solomon"), "wisdom")

    def test_song_of_solomon(self):
        self.assertEqual(bible_filename("Song of Solomon"), "songs")

    def test_esther_greek(self):
        self.assertEqual(bible_filename("Esther (Greek)"), "esther_greek")

    def test_ezra(self):
        self.assertEqual(bible_filename("1 Ezra"), "1ezra")
        self.assertEqual(bible_filename("2 Ezra"), "2ezra")

    def test_psalms(self):
        self.assertEqual(bible_filename("Psalms"), "psalms")

    def test_psalm_151(self):
        self.assertEqual(bible_filename("Psalm 151"), "psalm151")


class TestParseReadingReference(unittest.TestCase):
    def test_colon_verse_range(self):
        result = parse_reading_reference("Genesis 3:1-8")
        self.assertEqual(result, ("Genesis", 3, 1, 3, 8))

    def test_single_verse(self):
        result = parse_reading_reference("John 10:9")
        self.assertEqual(result, ("John", 10, 9, 10, 9))

    def test_dot_notation(self):
        result = parse_reading_reference("Exodus 15.22-16.1")
        self.assertEqual(result, ("Exodus", 15, 22, 16, 1))

    def test_bracket_kings(self):
        result = parse_reading_reference("3[1] Kings 2.6-14")
        self.assertEqual(result, ("1 Kings", 2, 6, 2, 14))

    def test_chapter_only(self):
        result = parse_reading_reference("Numbers 8")
        self.assertEqual(result, ("Numbers", 8, None, 8, None))

    def test_comma_chapters(self):
        result = parse_reading_reference("Exodus 12, 13")
        self.assertEqual(result, ("Exodus", 12, None, 13, None))

    def test_wisdom_shorthand(self):
        result = parse_reading_reference("Wisdom 7:1-5")
        self.assertEqual(result, ("Wisdom of Solomon", 7, 1, 7, 5))

    def test_cross_chapter(self):
        result = parse_reading_reference("Job 2:13-4:3")
        self.assertEqual(result, ("Job", 2, 13, 4, 3))

    def test_invalid_returns_none(self):
        self.assertIsNone(parse_reading_reference("not a reference"))

    def test_spaced_bracket_kings(self):
        result = parse_reading_reference("3 [1] Kings 17.1-23")
        self.assertEqual(result, ("1 Kings", 17, 1, 17, 23))

    def test_single_chapter_book_range(self):
        self.assertEqual(parse_reading_reference("Jude 1-10"), ("Jude", 1, 1, 1, 10))

    def test_noncontiguous_chapters_not_a_range(self):
        self.assertIsNone(parse_reading_reference("Exodus 12, 14"))


class TestHelpers(unittest.TestCase):
    def test_resolve_book_case_and_alias(self):
        self.assertEqual(resolve_book("john"), "John")
        self.assertEqual(resolve_book("PSALM"), "Psalms")
        self.assertEqual(resolve_book("1 kings"), "1 Kings")
        self.assertIsNone(resolve_book("nonsense"))

    def test_normalize_kings(self):
        self.assertEqual(normalize_kings("4 [2] Kings 2.1"), "2 Kings 2.1")

    def test_clean_readings(self):
        text = "Composite 1 - Genesis 1.1-5; 3 [1] Kings 18, 19 • John 1.1-5"
        self.assertEqual(clean_readings(text), ["Genesis 1.1-5", "1 Kings 18, 19", "John 1.1-5"])

    def test_clean_readings_bookless_continuation_and_zero_width(self):
        text = "\u200bComposite 19 - Micah 4.2-3, 5; 6.2-5, 8 • John 1.1-5"
        self.assertEqual(clean_readings(text), ["Micah 4.2-3, 5", "Micah 6.2-5, 8", "John 1.1-5"])

    def test_normalize_reference(self):
        self.assertEqual(normalize_reference("Job 42.12-17 (LXX)"), "Job 42.12-17")
        self.assertEqual(normalize_reference("Jeremiah (Baruch 3.35-4.4)"), "Baruch 3.35-4.4")

    def test_verse_to_next_chapter_part(self):
        self.assertEqual(parse_multi_reference("Luke 22.39-42, 45-23.1")[1], ("Luke", 22, 45, 23, 1))

    def test_parse_multi_reference(self):
        self.assertEqual(parse_multi_reference("Genesis 17.1-2, 4, 5-7"),
                         [("Genesis", 17, 1, 17, 2), ("Genesis", 17, 4, 17, 4), ("Genesis", 17, 5, 17, 7)])
        self.assertEqual(parse_multi_reference("Luke 2.20-21, 40-52")[1], ("Luke", 2, 40, 2, 52))
        with self.assertRaises(ValueError):
            parse_multi_reference("garbage, 4")


class TestParseBibleReference(unittest.TestCase):
    def test_book_only(self):
        self.assertEqual(parse_bible_reference(
            ["John"]), ("John", None, None, None))

    def test_book_and_chapter(self):
        self.assertEqual(parse_bible_reference(
            ["John", "3"]), ("John", 3, None, None))

    def test_book_chapter_verse(self):
        self.assertEqual(parse_bible_reference(
            ["John", "3:16"]), ("John", 3, 16, 16))

    def test_book_chapter_verse_range(self):
        self.assertEqual(parse_bible_reference(
            ["John", "3:16-17"]), ("John", 3, 16, 17))

    def test_dot_notation(self):
        self.assertEqual(parse_bible_reference(
            ["John", "3.16-17"]), ("John", 3, 16, 17))

    def test_multiword_book(self):
        self.assertEqual(parse_bible_reference(
            ["1", "Kings", "3:1"]), ("1 Kings", 3, 1, 1))

    def test_multiword_book_range(self):
        self.assertEqual(parse_bible_reference(
            ["1", "Kings", "3:1-5"]), ("1 Kings", 3, 1, 5))

    def test_multiword_book_chapter_only(self):
        self.assertEqual(parse_bible_reference(
            ["1", "Kings", "3"]), ("1 Kings", 3, None, None))

    def test_three_word_book(self):
        result = parse_bible_reference(["Wisdom", "of", "Solomon", "7:1"])
        self.assertEqual(result, ("Wisdom of Solomon", 7, 1, 1))

    def test_empty_args(self):
        self.assertEqual(parse_bible_reference([]), (None, None, None, None))

    def test_case_insensitive_book(self):
        self.assertEqual(parse_bible_reference(["john", "3:16"]), ("John", 3, 16, 16))

    def test_single_chapter_book_range(self):
        self.assertEqual(parse_bible_reference(["Jude", "1-10"]), ("Jude", 1, 1, 10))

    def test_invalid_chapter(self):
        result = parse_bible_reference(["John", "notanumber"])
        self.assertEqual(result, (None, None, None, None))


if __name__ == "__main__":
    unittest.main()
