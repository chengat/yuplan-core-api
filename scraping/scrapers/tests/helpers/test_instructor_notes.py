"""Test cases for helpers/instructor_notes.py"""

import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers.instructor_notes import parse_instructors, parse_notes


class TestParseInstructors(unittest.TestCase):
    """Test parse_instructors function"""
    
    def test_empty_string(self):
        self.assertEqual(parse_instructors(""), [])
    
    def test_none_input(self):
        self.assertEqual(parse_instructors(None), [])
    
    def test_single_instructor(self):
        self.assertEqual(parse_instructors("John Doe"), ["John Doe"])
    
    def test_comma_separated(self):
        result = parse_instructors("John Doe, Jane Smith")
        self.assertEqual(len(result), 2)
        self.assertIn("John Doe", result)
        self.assertIn("Jane Smith", result)
    
    def test_semicolon_separated(self):
        result = parse_instructors("John Doe; Jane Smith")
        self.assertEqual(len(result), 2)
    
    def test_pipe_separated(self):
        result = parse_instructors("John Doe|Jane Smith")
        self.assertEqual(len(result), 2)
    
    def test_br_tag_separated(self):
        result = parse_instructors("John Doe<br>Jane Smith")
        self.assertEqual(len(result), 2)
    
    def test_html_artifacts_filtered(self):
        result = parse_instructors("John Doe&nbsp;Jane Smith")
        self.assertNotIn("nbsp", [name.lower() for name in result])
    
    def test_mixed_separators(self):
        result = parse_instructors("John Doe, Jane Smith; Bob Johnson")
        self.assertEqual(len(result), 3)
    
    def test_whitespace_trimming(self):
        result = parse_instructors("  John Doe  ,  Jane Smith  ")
        self.assertIn("John Doe", result)
        self.assertIn("Jane Smith", result)


class TestParseNotes(unittest.TestCase):
    """Test parse_notes function"""
    
    def test_empty_string(self):
        self.assertEqual(parse_notes(""), "")
    
    def test_none_input(self):
        self.assertEqual(parse_notes(None), "")
    
    def test_plain_text(self):
        self.assertEqual(parse_notes("Prerequisites: EECS 1000"), "Prerequisites: EECS 1000")
    
    def test_br_tag_to_pipe(self):
        result = parse_notes("Line1<br>Line2")
        self.assertIn("|", result)
        self.assertIn("Line1", result)
        self.assertIn("Line2", result)
    
    def test_html_tags_stripped(self):
        result = parse_notes("<p>Prerequisites:</p> <strong>EECS 1000</strong>")
        self.assertNotIn("<p>", result)
        self.assertNotIn("</p>", result)
        self.assertIn("Prerequisites", result)
    
    def test_leading_trailing_pipes_stripped(self):
        result = parse_notes("<br>Text<br>")
        self.assertFalse(result.startswith("|"))
        self.assertFalse(result.endswith("|"))
    
    def test_multiple_br_tags(self):
        result = parse_notes("A<br>B<br>C")
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertIn("C", result)


if __name__ == '__main__':
    unittest.main()