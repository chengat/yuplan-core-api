"""Test cases for helpers/room_utils.py"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers.room_utils import clean_room


class TestCleanRoom(unittest.TestCase):
    """Test clean_room function"""
    
    def test_basic_room(self):
        self.assertEqual(clean_room("CB 101"), "CB 101")
    
    def test_room_with_whitespace(self):
        self.assertEqual(clean_room("  CB  101  "), "CB 101")
        self.assertEqual(clean_room("CB\n101"), "CB 101")
    
    def test_empty_string(self):
        self.assertEqual(clean_room(""), "")
    
    def test_room_with_html_entities(self):
        self.assertEqual(clean_room("CB&nbsp;101"), "CB 101")
    
    def test_room_with_multiple_spaces(self):
        self.assertEqual(clean_room("CB   101"), "CB 101")
    
    def test_room_with_special_characters(self):
        result = clean_room("CB-101/102")
        self.assertIn("CB", result)
        self.assertIn("101", result)


if __name__ == '__main__':
    unittest.main()