"""Test cases for helpers/text_utils.py"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers.text_utils import norm_text, html_to_text


class TestNormText(unittest.TestCase):
    """Test norm_text function"""
    
    def test_basic_text(self):
        self.assertEqual(norm_text("Hello World"), "Hello World")
    
    def test_html_entities(self):
        self.assertEqual(norm_text("&lt;div&gt;"), "<div>")
        self.assertEqual(norm_text("&amp;"), "&")
        self.assertEqual(norm_text("&quot;"), '"')
    
    def test_whitespace_collapsing(self):
        self.assertEqual(norm_text("Hello   World"), "Hello World")
        self.assertEqual(norm_text("Hello\n\nWorld"), "Hello World")
        self.assertEqual(norm_text("  Hello  \t  World  "), "Hello World")
    
    def test_none_input(self):
        self.assertEqual(norm_text(None), "")
    
    def test_empty_string(self):
        self.assertEqual(norm_text(""), "")
    
    def test_only_whitespace(self):
        self.assertEqual(norm_text("   \n\t  "), "")
    
    def test_mixed_entities_and_whitespace(self):
        self.assertEqual(norm_text("&lt;p&gt;  Hello   &amp;  World  &lt;/p&gt;"), "<p> Hello & World </p>")


class TestHtmlToText(unittest.TestCase):
    """Test html_to_text function"""
    
    def test_empty_string(self):
        self.assertEqual(html_to_text(""), "")
    
    def test_none_input(self):
        self.assertEqual(html_to_text(None), "")
    
    def test_plain_text(self):
        self.assertEqual(html_to_text("Hello World"), "Hello World")
    
    def test_br_tag_default_separator(self):
        self.assertEqual(html_to_text("Line1<br>Line2"), "Line1|Line2")
        self.assertEqual(html_to_text("Line1<br/>Line2"), "Line1|Line2")
        self.assertEqual(html_to_text("Line1<BR>Line2"), "Line1|Line2")
    
    def test_br_tag_custom_separator(self):
        self.assertEqual(html_to_text("Line1<br>Line2", br_separator=" / "), "Line1 / Line2")
    
    def test_strip_html_tags(self):
        self.assertEqual(html_to_text("<p>Hello</p>"), "Hello")
        self.assertEqual(html_to_text("<div><span>Hello</span></div>"), "Hello")
        self.assertEqual(html_to_text("<strong>Bold</strong> <em>Italic</em>"), "Bold Italic")
    
    def test_html_entities(self):
        self.assertEqual(html_to_text("&amp;"), "&")
        self.assertEqual(html_to_text("Test &amp; More"), "Test & More")

    def test_complex_html(self):
        html = "<div><p>Line1</p><br><p>Line2</p></div>"
        result = html_to_text(html)
        self.assertIn("Line1", result)
        self.assertIn("Line2", result)
    
    def test_whitespace_normalization(self):
        self.assertEqual(html_to_text("Hello    World"), "Hello World")
        self.assertEqual(html_to_text("  Hello  <br>  World  "), "Hello | World")


if __name__ == '__main__':
    unittest.main()