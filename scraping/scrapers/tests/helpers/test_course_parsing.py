"""Test cases for helpers/course_parsing.py"""

import unittest
import sys
from bs4 import BeautifulSoup
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from helpers.course_parsing import (
    is_header_row,
    parse_course_header,
    get_section_type,
    find_section_type_index,
    parse_section_row
)


class TestIsHeaderRow(unittest.TestCase):
    """Test is_header_row function"""
    
    def test_valid_header_row(self):
        html = """<tr>
            <td class="bodytext">Faculty</td>
            <td class="bodytext">Dept</td>
            <td class="bodytext">Term</td>
            <td class="bodytext" colspan="2">Course Title</td>
        </tr>"""
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        self.assertTrue(is_header_row(row))
    
    def test_non_header_row(self):
        html = """<tr>
            <td class="bodytext">LECT</td>
            <td class="bodytext">01</td>
        </tr>"""
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        self.assertFalse(is_header_row(row))
    
    def test_insufficient_cells(self):
        html = """<tr>
            <td class="bodytext">A</td>
            <td class="bodytext">B</td>
        </tr>"""
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        self.assertFalse(is_header_row(row))


class TestParseCourseHeader(unittest.TestCase):
    """Test parse_course_header function"""
    
    def test_basic_header(self):
        html = """<tr>
            <td class="bodytext">Faculty of Science</td>
            <td class="bodytext">EECS</td>
            <td class="bodytext">Fall 2024</td>
            <td class="bodytext">Introduction to Programming</td>
        </tr>"""
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        result = parse_course_header(row)
        
        self.assertEqual(result['faculty'], "Faculty of Science")
        self.assertEqual(result['department'], "EECS")
        self.assertEqual(result['term'], "Fall 2024")
        self.assertEqual(result['courseTitle'], "Introduction to Programming")
        self.assertEqual(result['sections'], [])


class TestGetSectionType(unittest.TestCase):
    """Test get_section_type function"""
    
    def test_lecture(self):
        self.assertEqual(get_section_type("LECT"), "LECT")
    
    def test_lab(self):
        self.assertEqual(get_section_type("LAB"), "LAB")
    
    def test_tutorial(self):
        self.assertEqual(get_section_type("TUTR"), "TUTR")


class TestFindSectionTypeIndex(unittest.TestCase):
    """Test find_section_type_index function"""
    
    def test_finds_lect(self):
        html = """<tr>
            <td>EECS 1000</td>
            <td>LECT</td>
            <td>01</td>
        </tr>"""
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        cells = row.find_all("td")
        
        index = find_section_type_index(cells)
        self.assertEqual(index, 1)
    
    def test_no_section_type(self):
        html = """<tr>
            <td>EECS 1000</td>
            <td>3.00</td>
        </tr>"""
        soup = BeautifulSoup(html, "html.parser")
        row = soup.find("tr")
        cells = row.find_all("td")
        
        index = find_section_type_index(cells)
        self.assertIsNone(index)


class TestParseSectionRow(unittest.TestCase):
    """Test parse_section_row function"""

    def test_section_row_with_schedule_table(self):
        header_html = """<tr>
            <td class=\"bodytext\">Faculty</td>
            <td class=\"bodytext\">EDUC</td>
            <td class=\"bodytext\">FW</td>
            <td class=\"bodytext\" colspan=\"2\">Test Course</td>
        </tr>"""
        course = parse_course_header(BeautifulSoup(header_html, "html.parser").find("tr"))

        row_html = """<tr>
            <td>1000 3.00 A</td>
            <td>EN</td>
            <td>LECT</td>
            <td>01</td>
            <td>E77J01</td>
            <td>
                <table>
                    <tr>
                        <td>F</td>
                        <td>8:30</td>
                        <td>170</td>
                        <td>Keele</td>
                        <td>WC 117</td>
                    </tr>
                </table>
            </td>
        </tr>"""
        row = BeautifulSoup(row_html, "html.parser").find("tr")
        detail = parse_section_row(row.find_all("td", recursive=False), course)

        self.assertIsNotNone(detail)
        self.assertEqual(course["courseId"], "1000")
        self.assertEqual(course["credits"], "3.00")
        self.assertEqual(course["languageOfInstruction"], "EN")
        self.assertEqual(detail["type"], "LECT")
        self.assertEqual(detail["meetNumber"], "01")
        self.assertEqual(detail["section"], "A")
        self.assertEqual(detail["catalogNumber"], "E77J01")
        self.assertEqual(detail["schedule"][0]["room"], "WC 117")

    def test_section_row_with_schedule_text(self):
        course = parse_course_header(BeautifulSoup("""<tr>
            <td class=\"bodytext\">Faculty</td>
            <td class=\"bodytext\">EDUC</td>
            <td class=\"bodytext\">FW</td>
            <td class=\"bodytext\" colspan=\"2\">Test Course</td>
        </tr>""", "html.parser").find("tr"))

        row_html = """<tr>
            <td>1001 3.00 B</td>
            <td>EN</td>
            <td>LECT</td>
            <td>02</td>
            <td>E77J02</td>
            <td>TBA</td>
        </tr>"""
        row = BeautifulSoup(row_html, "html.parser").find("tr")
        detail = parse_section_row(row.find_all("td", recursive=False), course)

        self.assertIsNotNone(detail)
        self.assertEqual(detail["schedule"][0]["time"], "TBA")

    def test_section_row_cancelled_notes(self):
        course = parse_course_header(BeautifulSoup("""<tr>
            <td class=\"bodytext\">Faculty</td>
            <td class=\"bodytext\">EDUC</td>
            <td class=\"bodytext\">FW</td>
            <td class=\"bodytext\" colspan=\"2\">Test Course</td>
        </tr>""", "html.parser").find("tr"))

        row_html = """<tr>
            <td>1002 3.00 C</td>
            <td>EN</td>
            <td>LECT</td>
            <td>03</td>
            <td>Cancelled</td>
            <td></td>
            <td>Cancelled due to weather</td>
        </tr>"""
        row = BeautifulSoup(row_html, "html.parser").find("tr")
        detail = parse_section_row(row.find_all("td", recursive=False), course)

        self.assertIsNotNone(detail)
        self.assertEqual(detail["catalogNumber"].lower(), "cancelled")
        self.assertEqual(detail["notes"], "Cancelled due to weather")

    def test_section_row_without_type_returns_none(self):
        course = parse_course_header(BeautifulSoup("""<tr>
            <td class=\"bodytext\">Faculty</td>
            <td class=\"bodytext\">EDUC</td>
            <td class=\"bodytext\">FW</td>
            <td class=\"bodytext\" colspan=\"2\">Test Course</td>
        </tr>""", "html.parser").find("tr"))

        row_html = """<tr>
            <td>1003 3.00 D</td>
            <td>EN</td>
            <td>04</td>
        </tr>"""
        row = BeautifulSoup(row_html, "html.parser").find("tr")
        detail = parse_section_row(row.find_all("td", recursive=False), course)
        self.assertIsNone(detail)


if __name__ == '__main__':
    unittest.main()