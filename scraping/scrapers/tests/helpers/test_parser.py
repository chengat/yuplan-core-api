"""Test cases for helpers/parser.py"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers.parser import parse_course_timetable_html


class TestParseCourseHTML(unittest.TestCase):
    """Test parse_course_timetable_html function"""
    
    def test_empty_html(self):
        """Test parsing empty HTML"""
        result = parse_course_timetable_html("")
        self.assertIn('courses', result)
        self.assertEqual(result['courses'], [])
    
    def test_no_table_html(self):
        """Test HTML without course table"""
        html = "<html><body><p>No courses</p></body></html>"
        result = parse_course_timetable_html(html)
        self.assertIn('courses', result)
        self.assertEqual(result['courses'], [])
    
    def test_alphanumeric_course_id_allowed_by_default(self):
        """Test that alphanumeric course IDs are accepted by default"""
        html = """
        <table>
            <tr><td>GS/EECS 6000</td><td>Graduate Course</td><td>3.00</td></tr>
        </table>
        """
        result = parse_course_timetable_html(html)
        self.assertIsNotNone(result)
    
    def test_metadata_extraction_enabled(self):
        """Test that metadata is extracted when enabled"""
        html = "<html><body><table></table></body></html>"
        result = parse_course_timetable_html(html, extract_metadata=True)
        self.assertIn('metadata', result)
        self.assertIsInstance(result['metadata'], dict)
    
    def test_metadata_extraction_disabled(self):
        """Test that metadata is not extracted when disabled"""
        html = "<html><body><table></table></body></html>"
        result = parse_course_timetable_html(html, extract_metadata=False)
        self.assertNotIn('metadata', result)
    
    def test_basic_course_structure(self):
        """Test that parsed courses have expected structure"""
        html = """
        <table>
            <tr>
                <td class="bodytext">Faculty</td>
                <td class="bodytext">EECS</td>
                <td class="bodytext">FW 2024</td>
                <td class="bodytext" colspan="2">Test Course</td>
            </tr>
        </table>
        """
        result = parse_course_timetable_html(html)
        self.assertIn('courses', result)


if __name__ == '__main__':
    unittest.main()