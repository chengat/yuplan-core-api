import io
import runpy
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

from bs4 import BeautifulSoup

from scraping.scrappers import graduate_studies


class TestHelpers(unittest.TestCase):
    def test_norm_text_basic_and_entities(self):
        self.assertEqual(graduate_studies.norm_text("  hello\nworld  "), "hello world")
        self.assertEqual(graduate_studies.norm_text("Tom &amp; Jerry"), "Tom & Jerry")

    def test_norm_text_none_returns_empty(self):
        self.assertEqual(graduate_studies.norm_text(None), "")

    def test_cell_text_none_and_nbsp(self):
        self.assertEqual(graduate_studies.cell_text(None), "")
        soup = BeautifulSoup("<td>Room&nbsp;101</td>", "html.parser")
        self.assertEqual(graduate_studies.cell_text(soup.td), "Room 101")

    def test_get_section_type_variants(self):
        self.assertEqual(graduate_studies.get_section_type("LEC"), "LECT")
        self.assertEqual(graduate_studies.get_section_type("Seminar"), "SEMR")
        self.assertEqual(graduate_studies.get_section_type("Online"), "ONLN")
        self.assertEqual(graduate_studies.get_section_type("ind study"), "ISTY")

    def test_get_section_type_no_match(self):
        self.assertEqual(graduate_studies.get_section_type("unknown"), "")

    def test_get_section_type_additional_types(self):
        self.assertEqual(graduate_studies.get_section_type("Blended"), "BLEN")
        self.assertEqual(graduate_studies.get_section_type("Co-op"), "COOP")
        self.assertEqual(graduate_studies.get_section_type("Field Exercise"), "FDEX")
        self.assertEqual(graduate_studies.get_section_type("Internship"), "INSP")
        self.assertEqual(graduate_studies.get_section_type("Research"), "RESP")
        self.assertEqual(graduate_studies.get_section_type("Hybrid Flex"), "HYFX")
        self.assertEqual(graduate_studies.get_section_type("ONCA"), "ONCA")

    def test_html_to_text_br_and_unescape(self):
        html_fragment = "Line1&lt;br&gt;Line2<br>Line&nbsp;3"
        self.assertEqual(graduate_studies.html_to_text(html_fragment, br_separator="|"), "Line1|Line2|Line 3")

    def test_html_to_text_empty(self):
        self.assertEqual(graduate_studies.html_to_text(""), "")

    def test_parse_instructors_mixed_separators(self):
        html_fragment = "Prof One &amp; Prof Two; Prof Three|Prof Four"
        self.assertEqual(
            graduate_studies.parse_instructors(html_fragment),
            ["Prof One", "Prof Two", "Prof Three", "Prof Four"],
        )

    def test_parse_instructors_empty(self):
        self.assertEqual(graduate_studies.parse_instructors(""), [])

    def test_parse_instructors_filters_html_entities(self):
        result = graduate_studies.parse_instructors("&nbsp;&amp;lt;&gt;")
        # After parsing, most HTML entities are filtered
        self.assertTrue(all(name not in {"nbsp", "amp", "lt", "gt"} for name in result))

    def test_parse_notes_br_preserves_separator(self):
        html_fragment = "Bring laptop<br>Arrive early"
        self.assertEqual(graduate_studies.parse_notes(html_fragment), "Bring laptop | Arrive early")

    def test_parse_notes_empty(self):
        self.assertEqual(graduate_studies.parse_notes(""), "")

    def test_clean_room_round_trip(self):
        self.assertEqual(graduate_studies.clean_room(" ACE101 "), "ACE101")

    def test_is_header_row_true_and_false(self):
        soup = BeautifulSoup(
            """
            <tr>
              <td class="bodytext">A</td><td class="bodytext">B</td>
              <td class="bodytext">C</td><td class="bodytext" colspan="3">D</td>
            </tr>
            """,
            "html.parser",
        )
        self.assertTrue(graduate_studies.is_header_row(soup.tr))

        soup2 = BeautifulSoup("<tr><td class='bodytext'>X</td><td>Y</td></tr>", "html.parser")
        self.assertFalse(graduate_studies.is_header_row(soup2.tr))

    def test_parse_course_header_fields(self):
        soup = BeautifulSoup(
            """
            <tr>
              <td class="bodytext">GS</td>
              <td class="bodytext">EDUC</td>
              <td class="bodytext">FW25</td>
              <td class="bodytext" colspan="3">Advanced Education Theory</td>
            </tr>
            """,
            "html.parser",
        )
        course = graduate_studies.parse_course_header(soup.tr)
        self.assertEqual(course["faculty"], "GS")
        self.assertEqual(course["department"], "EDUC")
        self.assertEqual(course["term"], "FW25")
        self.assertEqual(course["courseTitle"], "Advanced Education Theory")

    def test_find_section_type_index_found_and_missing(self):
        soup = BeautifulSoup("<tr><td>foo</td><td>LEC</td><td>bar</td></tr>", "html.parser")
        row_cells = soup.find_all("td")
        self.assertEqual(graduate_studies.find_section_type_index(row_cells), 1)

        soup2 = BeautifulSoup("<tr><td>foo</td><td>bar</td></tr>", "html.parser")
        self.assertIsNone(graduate_studies.find_section_type_index(soup2.find_all("td")))

    def test_fill_course_summary_and_loi_populates(self):
        soup = BeautifulSoup("<tr><td>5001 3.00 A</td><td>EN</td><td>LEC</td></tr>", "html.parser")
        row_cells = soup.find_all("td")
        course = {"courseId": "", "credits": "", "section": "", "languageOfInstruction": ""}
        section_letter = graduate_studies.fill_course_summary_and_loi(row_cells, section_type_index=2, course=course)
        self.assertEqual(course["courseId"], "5001")
        self.assertEqual(course["credits"], "3.00")
        self.assertEqual(section_letter, "A")
        self.assertEqual(course["languageOfInstruction"], "EN")

    def test_fill_course_summary_and_loi_alphanumeric_course_id(self):
        soup = BeautifulSoup("<tr><td>4800Q 3.00 A</td><td>EN</td><td>SEMR</td></tr>", "html.parser")
        row_cells = soup.find_all("td")
        course = {"courseId": "", "credits": "", "section": "", "languageOfInstruction": ""}
        section_letter = graduate_studies.fill_course_summary_and_loi(row_cells, section_type_index=2, course=course)
        self.assertEqual(course["courseId"], "4800Q")
        self.assertEqual(course["credits"], "3.00")
        self.assertEqual(section_letter, "A")

    def test_fill_course_summary_and_loi_preserves_existing(self):
        soup = BeautifulSoup("<tr><td>9999 4.00 Z</td><td>FR</td><td>LEC</td></tr>", "html.parser")
        row_cells = soup.find_all("td")
        course = {"courseId": "5001", "credits": "3.00", "section": "A", "languageOfInstruction": "EN"}
        section_letter = graduate_studies.fill_course_summary_and_loi(row_cells, section_type_index=2, course=course)
        self.assertEqual(course["courseId"], "5001")
        self.assertEqual(course["credits"], "3.00")
        self.assertEqual(course["languageOfInstruction"], "EN")

    def test_maybe_extract_cancelled_notes_from_offset(self):
        soup = BeautifulSoup(
            """
            <tr>
              <td>LEC</td>
              <td></td>
              <td></td>
              <td></td>
              <td>Note from offset</td>
              <td>Backup note</td>
            </tr>
            """,
            "html.parser",
        )
        row_cells = soup.find_all("td")
        notes = graduate_studies.maybe_extract_cancelled_notes(row_cells, section_type_index=0, notes="")
        self.assertEqual(notes, "Note from offset")

    def test_maybe_extract_cancelled_notes_keeps_existing(self):
        soup = BeautifulSoup("<tr><td>LEC</td><td>X</td><td>Y</td></tr>", "html.parser")
        row_cells = soup.find_all("td")
        self.assertEqual(graduate_studies.maybe_extract_cancelled_notes(row_cells, 0, "Already"), "Already")

    def test_parse_schedule_entry(self):
        soup = BeautifulSoup(
            """
            <tr>
              <td>Mon</td>
              <td>12:00</td>
              <td>1h</td>
              <td>KEELE</td>
              <td>ACE101</td>
            </tr>
            """,
            "html.parser",
        )
        schedule_cells = soup.find_all("td")
        entry = graduate_studies.parse_schedule_entry(schedule_cells)
        self.assertEqual(entry["day"], "Mon")
        self.assertEqual(entry["time"], "12:00")
        self.assertEqual(entry["duration"], "1h")
        self.assertEqual(entry["campus"], "KEELE")
        self.assertEqual(entry["room"], "ACE101")


class TestParser(unittest.TestCase):
    def test_parse_section_row_without_section_type_returns_none(self):
        soup = BeautifulSoup("<tr><td>foo</td><td>bar</td></tr>", "html.parser")
        row_cells = soup.find_all("td")
        course = {"courseId": "", "credits": "", "section": "", "languageOfInstruction": ""}
        self.assertIsNone(graduate_studies.parse_section_row(row_cells, course))

    def test_parse_section_row_returns_none_when_no_content(self):
        calls = iter(["LECT", ""])

        def fake_get_section_type(_text):
            return next(calls, "")

        with mock.patch.object(graduate_studies, "get_section_type", side_effect=fake_get_section_type):
            soup = BeautifulSoup("<tr><td>Lect</td></tr>", "html.parser")
            row_cells = soup.find_all("td")
            course = {"courseId": "", "credits": "", "section": "", "languageOfInstruction": "", "sections": []}
            self.assertIsNone(graduate_studies.parse_section_row(row_cells, course))

    def test_parse_section_row_flat_schedule_text(self):
        soup = BeautifulSoup(
            """
            <tr>
              <td>5001 3.00 A</td>
              <td>EN</td>
              <td>LEC</td>
              <td>01</td>
              <td>A01</td>
              <td>Wednesday 18:00</td>
            </tr>
            """,
            "html.parser",
        )
        row_cells = soup.find_all("td")
        course = {"courseId": "", "credits": "", "section": "", "languageOfInstruction": ""}
        section = graduate_studies.parse_section_row(row_cells, course)
        self.assertIsNotNone(section)
        self.assertEqual(section["type"], "LECT")
        self.assertEqual(section["catalogNumber"], "A01")
        self.assertEqual(section["schedule"], [{"day": "", "time": "Wednesday 18:00", "duration": "", "campus": "", "room": ""}])
        self.assertEqual(course["courseId"], "5001")
        self.assertEqual(course["credits"], "3.00")
        self.assertEqual(course["languageOfInstruction"], "EN")

    def test_parse_course_timetable_html_minimal(self):
        html_content = """
        <html>
          <body>
            <p class="heading">Graduate Studies Timetable</p>
            <p class="bodytext"><strong>2025-12-01</strong></p>
            <table>
              <tr>
                <td class="bodytext">GS</td>
                <td class="bodytext">EDUC</td>
                <td class="bodytext">FW25</td>
                <td class="bodytext" colspan="6">Advanced Education Theory</td>
              </tr>
              <tr>
                <td>5001 3.00 A</td><td>EN</td><td>LEC</td><td>01</td><td>A01</td>
                <td>
                  <table>
                    <tr><td>Mon</td><td>12:00</td><td>1h</td><td>KEELE</td><td>ACE101</td></tr>
                  </table>
                  <td>Prof One<br>Prof Two</td>
                  <td>Bring laptop</td>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """

        result = graduate_studies.parse_course_timetable_html(html_content)
        courses = result.get("courses", [])
        self.assertEqual(len(courses), 1)

        course = courses[0]
        self.assertEqual(course["faculty"], "GS")
        self.assertEqual(course["department"], "EDUC")
        self.assertEqual(course["term"], "FW25")
        self.assertEqual(course["courseTitle"], "Advanced Education Theory")
        self.assertEqual(course["courseId"], "5001")
        self.assertEqual(course["credits"], "3.00")
        self.assertEqual(course["languageOfInstruction"], "EN")

        self.assertEqual(len(course["sections"]), 1)
        section = course["sections"][0]
        self.assertEqual(section["type"], "LECT")
        self.assertEqual(section["meetNumber"], "01")
        self.assertEqual(section["catalogNumber"], "A01")
        self.assertEqual(section["instructors"], ["Prof One", "Prof Two"])
        self.assertEqual(section["notes"], "Bring laptop")
        self.assertEqual(section["section"], "A")

        self.assertEqual(len(section["schedule"]), 1)
        entry = section["schedule"][0]
        self.assertEqual(entry["day"], "Mon")
        self.assertEqual(entry["time"], "12:00")
        self.assertEqual(entry["duration"], "1h")
        self.assertEqual(entry["campus"], "KEELE")
        self.assertEqual(entry["room"], "ACE101")

    def test_parse_course_timetable_html_cancelled_section(self):
        html_content = """
        <html>
          <body>
            <p class="heading">Graduate Studies Timetable</p>
            <p class="bodytext"><strong>2025-12-01</strong></p>
            <table>
              <tr>
                <td class="bodytext">GS</td>
                <td class="bodytext">EDUC</td>
                <td class="bodytext">FW25</td>
                <td class="bodytext" colspan="6">Advanced Education Theory</td>
              </tr>
              <tr>
                <td>5001 3.00 A</td>
                <td>EN</td>
                <td>LEC</td>
                <td>01</td>
                <td>cancelled</td>
                <td></td>
                <td>Cancelled due to weather</td>
              </tr>
            </table>
          </body>
        </html>
        """

        result = graduate_studies.parse_course_timetable_html(html_content)
        courses = result.get("courses", [])
        self.assertEqual(len(courses), 1)
        course = courses[0]
        self.assertEqual(len(course["sections"]), 1)
        section = course["sections"][0]
        self.assertEqual(section["type"], "LECT")
        self.assertEqual(section["catalogNumber"], "cancelled")
        self.assertEqual(section["notes"], "Cancelled due to weather")
        self.assertEqual(section["schedule"], [])
        self.assertEqual(section["instructors"], [])

    def test_parse_course_timetable_html_no_table(self):
        html_content = """
        <html>
          <body>
            <p class="heading">Graduate Studies Timetable</p>
            <p class="bodytext"><strong>2025-12-01</strong></p>
          </body>
        </html>
        """
        result = graduate_studies.parse_course_timetable_html(html_content)
        self.assertEqual(result.get("courses"), [])

    def test_parse_course_timetable_html_skips_non_rows_and_breaks_at_header(self):
        html = """
        <html><body>
        <table>
          <tr>
            <td class="bodytext">GS</td>
            <td class="bodytext">EDUC</td>
            <td class="bodytext">FW25</td>
            <td class="bodytext" colspan="2">Course One</td>
          </tr>
          <div>Should be skipped</div>
          <tr></tr>
          <tr>
            <td class="bodytext">GS</td>
            <td class="bodytext">EDUC</td>
            <td class="bodytext">FW25</td>
            <td class="bodytext" colspan="2">Course Two</td>
          </tr>
        </table>
        </body></html>
        """

        result = graduate_studies.parse_course_timetable_html(html)

        self.assertEqual(len(result["courses"]), 2)
        self.assertEqual(result["courses"][0]["sections"], [])
        self.assertEqual(result["courses"][1]["courseTitle"], "Course Two")

    def test_parse_course_timetable_html_header_guards(self):
        class DummyRow:
            name = "tr"

            def __init__(self):
                self._next = []

            def set_next(self, items):
                self._next = items

            @property
            def next_elements(self):
                return iter(self._next)

            def find_all(self, *args, **kwargs):
                return []

        class DummyTable:
            def __init__(self, rows):
                self.rows = rows

            def find_all(self, *args, **kwargs):
                return self.rows

        dummy1 = DummyRow()
        dummy2 = DummyRow()
        dummy3 = DummyRow()
        dummy1.set_next([dummy1, dummy3, dummy2])
        dummy2.set_next([])
        dummy3.set_next([])
        dummy_table = DummyTable([dummy1, dummy2])

        class DummySoup:
            def select_one(self, *_args, **_kwargs):
                return None

            def select(self, *_args, **_kwargs):
                return []

            def find(self, *_args, **_kwargs):
                return dummy_table

        def fake_is_header_row(element):
            return element in {dummy1, dummy2}

        with mock.patch.object(graduate_studies, "BeautifulSoup", return_value=DummySoup()), \
            mock.patch.object(graduate_studies, "is_header_row", side_effect=fake_is_header_row), \
            mock.patch.object(graduate_studies, "parse_course_header", return_value={"sections": [], "courseId": "", "credits": "", "section": "", "languageOfInstruction": "", "courseTitle": "", "faculty": "", "department": "", "term": ""}), \
            mock.patch.object(graduate_studies, "Tag", (graduate_studies.Tag, DummyRow)):
            result = graduate_studies.parse_course_timetable_html("ignored")

        self.assertEqual(len(result["courses"]), 2)
        self.assertEqual(result["courses"][0]["sections"], [])

    def test_build_details_cancelled_text(self):
        soup = BeautifulSoup(
            """
            <tr>
              <td>LEC</td>
              <td>01</td>
              <td>cancelled</td>
              <td>some schedule</td>
            </tr>
            """,
            "html.parser",
        )
        row_cells = soup.find_all("td")
        schedule, instructors, notes, catalog_number, is_cancelled = graduate_studies.build_details(row_cells, 0)
        
        self.assertEqual(catalog_number, "cancelled")
        self.assertTrue(is_cancelled)

    def test_build_details_with_inner_table(self):
        soup = BeautifulSoup(
            """
            <tr>
              <td>LEC</td>
              <td>01</td>
              <td>A01</td>
              <td>
                <table>
                  <tr><td>Mon</td><td>12:00</td><td>1h</td><td>KEELE</td><td>ACE101</td></tr>
                </table>
                <td>Prof One</td>
                <td>Notes here</td>
              </td>
            </tr>
            """,
            "html.parser",
        )
        row_cells = soup.find_all("td")
        schedule, instructors, notes, catalog_number, is_cancelled = graduate_studies.build_details(row_cells, 0)
        
        self.assertEqual(catalog_number, "A01")
        self.assertFalse(is_cancelled)
        self.assertEqual(len(schedule), 1)
        self.assertEqual(schedule[0]["day"], "Mon")
        self.assertEqual(instructors, ["Prof One"])
        self.assertEqual(notes, "Notes here")

    def test_make_section_detail_with_section_letter(self):
        soup = BeautifulSoup("<tr><td>LEC</td><td>01</td><td>A01</td></tr>", "html.parser")
        row_cells = soup.find_all("td")
        section_detail = graduate_studies.make_section_detail(
            row_cells, 0, "LECT", "A", "A01", [], [], ""
        )
        self.assertEqual(section_detail["type"], "LECT")
        self.assertEqual(section_detail["meetNumber"], "01")
        self.assertEqual(section_detail["section"], "A")
        self.assertEqual(section_detail["catalogNumber"], "A01")

    def test_make_section_detail_without_section_letter(self):
        soup = BeautifulSoup("<tr><td>LEC</td><td>01</td><td>A01</td></tr>", "html.parser")
        row_cells = soup.find_all("td")
        section_detail = graduate_studies.make_section_detail(
            row_cells, 0, "LECT", "", "A01", [], [], ""
        )
        self.assertEqual(section_detail["type"], "LECT")
        self.assertNotIn("section", section_detail)
        self.assertEqual(section_detail["catalogNumber"], "A01")

    def test_main_happy_path(self):
        tmpdir = tempfile.mkdtemp()
        try:
            scraping_dir = Path(tmpdir) / "scraping"
            scrappers_dir = scraping_dir / "scrappers"
            page_source = scraping_dir / "page_source"
            data_dir = scraping_dir / "data"
            scrappers_dir.mkdir(parents=True, exist_ok=True)
            page_source.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)

            html_path = page_source / "graduate_studies.html"
            html_path.write_text(
                """
                <html><body>
                  <p class="heading">Graduate Studies Timetable</p>
                  <p class="bodytext"><strong>2025-12-01</strong></p>
                  <table>
                    <tr>
                      <td class="bodytext">GS</td>
                      <td class="bodytext">EDUC</td>
                      <td class="bodytext">FW25</td>
                      <td class="bodytext" colspan="6">Title</td>
                    </tr>
                    <tr>
                      <td>5001 3.00 A</td><td>EN</td><td>LEC</td><td>01</td><td>A01</td>
                      <td><table><tr><td>Mon</td><td>12:00</td><td>1h</td><td>KEELE</td><td>ACE101</td></tr></table></td>
                    </tr>
                  </table>
                </body></html>
                """,
                encoding="utf-8",
            )

            original_file = graduate_studies.__file__ if hasattr(graduate_studies, "__file__") else None
            graduate_studies.__file__ = str(scrappers_dir / "graduate_studies.py")
            buf = io.StringIO()
            with redirect_stdout(buf):
                graduate_studies.main()
            output = buf.getvalue()
            written = (data_dir / "graduate_studies.json").read_text(encoding="utf-8")
            self.assertIn("Saved:", output)
            self.assertIn("Courses: 1", output)
            self.assertIn("graduate_studies.json", output)
            self.assertIn("\"courses\"", written)
        finally:
            if original_file is not None:
                graduate_studies.__file__ = original_file
            shutil.rmtree(tmpdir)

    def test_main_read_error(self):
        tmpdir = tempfile.mkdtemp()
        try:
            scraping_dir = Path(tmpdir) / "scraping"
            scrappers_dir = scraping_dir / "scrappers"
            scrappers_dir.mkdir(parents=True, exist_ok=True)
            original_file = graduate_studies.__file__ if hasattr(graduate_studies, "__file__") else None
            graduate_studies.__file__ = str(scrappers_dir / "graduate_studies.py")
            buf = io.StringIO()
            with redirect_stdout(buf):
                graduate_studies.main()
            output = buf.getvalue()
            self.assertIn("Error reading HTML", output)
        finally:
            if original_file is not None:
                graduate_studies.__file__ = original_file
            shutil.rmtree(tmpdir)

    def test_main_handles_parse_error_with_traceback(self):
        with mock.patch.object(graduate_studies, "parse_course_timetable_html", side_effect=ValueError("boom")):
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                graduate_studies.main()
            output = buf.getvalue()
            self.assertIn("Error parsing HTML: boom", output)
            self.assertIn("ValueError: boom", output)

    def test_entrypoint_runs_under_main_guard(self):
        dummy_html = """
        <html><body>
        <p class="heading">Sample</p>
        <p class="bodytext"><strong>Updated</strong></p>
        <table>
          <tr>
            <td class="bodytext">GS</td>
            <td class="bodytext">EDUC</td>
            <td class="bodytext">FW25</td>
            <td class="bodytext" colspan="2">Course One</td>
          </tr>
        </table>
        </body></html>
        """

        writes = []

        with mock.patch("pathlib.Path.read_text", return_value=dummy_html), mock.patch("pathlib.Path.write_text", lambda self, text, encoding="utf-8": writes.append((self, text)) or len(text)):
            buf = io.StringIO()
            with redirect_stdout(buf):
                runpy.run_path(str(Path(graduate_studies.__file__)), run_name="__main__")
            output = buf.getvalue()

        self.assertIn("Saved:", output)
        self.assertTrue(writes)

    def test_main_except_block_via_manual_call(self):
        dummy_globals = runpy.run_path(str(Path(graduate_studies.__file__)), run_name="not_main")
        main_func = dummy_globals["main"]
        main_func.__globals__["parse_course_timetable_html"] = mock.Mock(side_effect=RuntimeError("boom"))

        with mock.patch("pathlib.Path.read_text", return_value="<html></html>"), mock.patch("pathlib.Path.write_text", return_value=0):
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                main_func()
            output = buf.getvalue()

        self.assertIn("Error parsing HTML: boom", output)
        self.assertIn("RuntimeError: boom", output)


if __name__ == "__main__":
    unittest.main()

