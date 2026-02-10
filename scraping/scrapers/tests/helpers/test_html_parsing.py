"""Test cases for helpers/html_parsing.py"""

import unittest
import sys
from bs4 import BeautifulSoup
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers.html_parsing import cell_text


class TestCellText(unittest.TestCase):
    """Test cell_text function"""
    
    def test_none_element(self):
        self.assertEqual(cell_text(None), "")
    
    def test_simple_text(self):
        soup = BeautifulSoup("<td>Hello</td>", "html.parser")
        element = soup.find("td")
        self.assertEqual(cell_text(element), "Hello")
    
    def test_nested_tags(self):
        soup = BeautifulSoup("<td><span>Hello</span> <strong>World</strong></td>", "html.parser")
        element = soup.find("td")
        self.assertEqual(cell_text(element), "Hello World")
    
    def test_nbsp_replacement(self):
        soup = BeautifulSoup("<td>Hello&nbsp;World</td>", "html.parser")
        element = soup.find("td")
        self.assertEqual(cell_text(element), "Hello World")
    
    def test_whitespace_normalization(self):
        soup = BeautifulSoup("<td>Hello   \n  World</td>", "html.parser")
        element = soup.find("td")
        self.assertEqual(cell_text(element), "Hello World")
    
    def test_empty_element(self):
        soup = BeautifulSoup("<td></td>", "html.parser")
        element = soup.find("td")
        self.assertEqual(cell_text(element), "")
    
    def test_multiple_nbsp(self):
        soup = BeautifulSoup("<td>A&nbsp;&nbsp;&nbsp;B</td>", "html.parser")
        element = soup.find("td")
        result = cell_text(element)
        self.assertIn("A", result)
        self.assertIn("B", result)


if __name__ == '__main__':
    unittest.main()