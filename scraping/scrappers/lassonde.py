import json
import re
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any
import html
from pathlib import Path


def norm_text(text: str) -> str:
    if text is None:
        return ""
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def cell_text(element) -> str:
    if element is None:
        return ""
    text = element.get_text(" ", strip=True)
    text = text.replace("\xa0", " ")
    return norm_text(text)


def html_to_text(html_fragment: str, br_separator: str = "|") -> str:
    if not html_fragment:
        return ""
    text = re.sub(r"<br\s*/?>", br_separator, html_fragment, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_header_row(table_row: Tag) -> bool:
    """Return True if a row is a course header.
    A header row has 4 bodytext TDs and the 4th has colspan.
    """
    cells = table_row.find_all("td", class_="bodytext", recursive=False)
    return len(cells) >= 4 and cells[3].has_attr("colspan")


def parse_course_header(header_row: Tag) -> Dict[str, Any]:
    """Parse the course header row into a base course dictionary."""
    cells = header_row.find_all("td", class_="bodytext", recursive=False)
    return {
        "faculty": cell_text(cells[0]),
        "department": cell_text(cells[1]),
        "term": cell_text(cells[2]),
        "courseTitle": cell_text(cells[3]),
        "courseId": "",
        "credits": "",
        "section": "",
        "languageOfInstruction": "",
        "sections": [],
    }


def parse_section_row(row_cells: List[Tag], course: Dict[str, Any]) -> Dict[str, Any] | None:
    """Parse a section row into a detail dict and update course summary/LOI.
    Returns a section detail or None if the row doesn't contain a section type.
    """
    # 1) Locate the section type column
    section_type_index = find_section_type_index(row_cells)
    if section_type_index is None:
        return None

    # 2) Update course summary (courseId/credits/section) and LOI
    fill_course_summary_and_loi(row_cells, section_type_index, course)

    # 3) Determine section type
    section_type = get_section_type(cell_text(row_cells[section_type_index]))

    # 4) Build schedule/instructors/notes and catalog
    schedule, instructors, notes, catalog_number, is_cancelled = build_details(row_cells, section_type_index)

    # 5) Extract notes for cancelled entries (malformed sibling TDs)
    notes = maybe_extract_cancelled_notes(row_cells, section_type_index, notes) if is_cancelled and not notes else notes

    # 6) Build section detail and return if non-empty
    section_detail = make_section_detail(row_cells, section_type_index, section_type, catalog_number, schedule, instructors, notes)
    if section_type or section_detail["meetNumber"] or section_detail["catalogNumber"] or section_detail["schedule"] or section_detail["instructors"] or section_detail["notes"]:
        return section_detail
    return None


def find_section_type_index(row_cells: List[Tag]) -> int | None:
    for idx, cell in enumerate(row_cells):
        if get_section_type(cell_text(cell)):
            return idx
    return None


def fill_course_summary_and_loi(row_cells: List[Tag], section_type_index: int, course: Dict[str, Any]) -> None:
    if not course["courseId"] or not course["credits"] or not course["section"]:
        summary_pattern = re.compile(r"(\d{3,4})\s+([0-9]+\.[0-9]{2})\s*([A-Z0-9]?)")
        for j in range(section_type_index - 1, -1, -1):
            match = summary_pattern.search(cell_text(row_cells[j]))
            if match:
                course_id, credits, section_letter = match.group(1), match.group(2), match.group(3)
                course["courseId"] = course_id or course["courseId"]
                course["credits"] = credits or course["credits"]
                course["section"] = section_letter or course["section"]
                break

    if not course["languageOfInstruction"]:
        for j in range(section_type_index - 1, -1, -1):
            token = cell_text(row_cells[j])
            if 1 < len(token) <= 3 and token.isupper() and token.isalpha():
                course["languageOfInstruction"] = token
                break


def build_details(row_cells: List[Tag], section_type_index: int) -> tuple[List[Dict[str, str]], List[str], str, str, bool]:
    schedule: List[Dict[str, str]] = []
    catalog_cell = row_cells[section_type_index + 2] if len(row_cells) > section_type_index + 2 else None
    schedule_cell = row_cells[section_type_index + 3] if len(row_cells) > section_type_index + 3 else None
    instructors: List[str] = []
    notes = ""

    catalog_number = cell_text(catalog_cell) if catalog_cell else ""
    is_cancelled = catalog_number.lower() == "cancelled"

    if schedule_cell is not None:
        inner_table = schedule_cell.find("table")
        if inner_table:
            for s_tr in inner_table.find_all("tr"):
                s_tds = s_tr.find_all("td")
                if len(s_tds) >= 5:
                    entry = {
                        "day": cell_text(s_tds[0]),
                        "time": cell_text(s_tds[1]),
                        "duration": cell_text(s_tds[2]),
                        "campus": cell_text(s_tds[3]),
                        "room": clean_room(cell_text(s_tds[4])),
                    }
                    if any(entry.values()):
                        schedule.append(entry)
        else:
            schedule_text = cell_text(schedule_cell)
            if schedule_text and schedule_text.lower() != "cancelled":
                schedule.append({"day": "", "time": schedule_text, "duration": "", "campus": "", "room": ""})

        nested_tds = schedule_cell.find_all("td", recursive=False)
        if len(nested_tds) >= 1:
            instructors = parse_instructors(nested_tds[0].decode_contents())
        if len(nested_tds) >= 2:
            notes = parse_notes(nested_tds[1].decode_contents())

    return schedule, instructors, notes, catalog_number, is_cancelled


def maybe_extract_cancelled_notes(row_cells: List[Tag], section_type_index: int, notes: str) -> str:
    for offset in [4, 5]:
        if len(row_cells) > section_type_index + offset:
            potential_notes = parse_notes(row_cells[section_type_index + offset].decode_contents())
            if potential_notes and potential_notes.strip():
                return potential_notes
    return notes


def make_section_detail(row_cells: List[Tag], section_type_index: int, section_type: str, catalog_number: str, schedule: List[Dict[str, str]], instructors: List[str], notes: str) -> Dict[str, Any]:
    return {
        "type": section_type,
        "meetNumber": cell_text(row_cells[section_type_index + 1]) if len(row_cells) > section_type_index + 1 else "",
        "catalogNumber": catalog_number,
        "schedule": schedule,
        "instructors": instructors,
        "notes": notes,
    }


def get_section_type(text: str) -> str:
    normalized_text = norm_text(text).upper()
    compact_text = re.sub(r"[^A-Z]", "", normalized_text)
    section_types = [
        ("LECT", "LECT"), ("LEC", "LECT"),
        ("LAB", "LAB"),
        ("TUTR", "TUTR"), ("TUT", "TUTR"),
        ("SEMR", "SEMR"), ("SEMINAR", "SEMR"), ("SEM", "SEMR"),
        ("WRKS", "WRKS"), ("WRK", "WRKS"), ("WORKSHOP", "WRKS"),
        ("PRAC", "PRAC"), ("PRA", "PRAC"),
        ("BLEN", "BLEN"), ("BLENDED", "BLEN"),
        ("ONLN", "ONLN"), ("ONLINE", "ONLN"), ("ONL", "ONLN"),
        ("COOP", "COOP"), ("COOPTERM", "COOP"), ("COOPWORKTERM", "COOP"),
        ("ISTY", "ISTY"), ("INDEPENDENTSTUDY", "ISTY"), ("INDSTUDY", "ISTY"),
        ("FDEX", "FDEX"), ("FIELDEXERCISE", "FDEX"),
        ("INSP", "INSP"), ("INTERNSHIP", "INSP"),
        ("RESP", "RESP"), ("RESEARCH", "RESP"),
        ("STUDIO", "STUDIO"),
        ("CLIN", "CLIN"), ("CLINICAL", "CLIN"),
    ]
    for pattern, normalized_type in section_types:
        if pattern in compact_text:
            return normalized_type
    return ""


def parse_instructors(instructor_html: str) -> List[str]:
    if not instructor_html:
        return []
    text = html_to_text(instructor_html, br_separator="|")
    parts = re.split(r"[|,;&]", text)
    instructors_list: List[str] = []
    for part in parts:
        name = norm_text(part)
        if name and name.lower() not in {"nbsp", "amp", "lt", "gt"}:
            instructors_list.append(name)
    return instructors_list


def parse_notes(notes_html: str) -> str:
    if not notes_html:
        return ""
    text = html_to_text(notes_html, br_separator=" | ")
    return text.strip(" |")


def clean_room(room_text: str) -> str:
    cleaned_text = norm_text(room_text)
    return cleaned_text


def parse_course_timetable_html(html_content: str) -> Dict[str, Any]:
    """Parse the Lassonde timetable HTML into a structured JSON-friendly dict.
    Relies on header rows to segment courses, then walks subsequent rows,
    extracting section details with robust handling of malformed HTML.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    title = cell_text(soup.select_one("p.heading"))
    last_updated = ""
    for p in soup.select("p.bodytext"):
        strong = p.find("strong")
        if strong:
            last_updated = cell_text(strong)
            break

    table = soup.find("table")
    if not table:
        return {"metadata": {"title": title, "lastUpdated": last_updated, "source": "York University"}, "courses": []}

    # Orchestrate parsing with module-level helpers
    courses: List[Dict[str, Any]] = []
    header_rows = [tr for tr in table.find_all("tr") if is_header_row(tr)]
    for header in header_rows:
        course = parse_course_header(header)
        for element in header.next_elements:
            if not isinstance(element, Tag):
                continue
            if element is header:
                continue
            if element.name != "tr":
                continue
            if is_header_row(element):
                break
            row_cells = element.find_all("td", recursive=False)
            if not row_cells:
                continue
            section_detail = parse_section_row(row_cells, course)
            if section_detail is not None:
                course["sections"].append(section_detail)
        courses.append(course)

    return {"metadata": {"title": title, "lastUpdated": last_updated, "source": "York University"}, "courses": courses}


def main():
    scraping_dir = Path(__file__).resolve().parents[1]
    html_path = scraping_dir / "page_source" / "lassonde.html"
    data_path = scraping_dir / "data" / "lassonde.json"

    try:
        html_content = html_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as error:
        print(f"Error reading HTML: {error}")
        return

    try:
        result = parse_course_timetable_html(html_content)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved: {data_path}")
        print(f"Courses: {len(result.get('courses', []))}")
        for index, course in enumerate(result.get('courses', []), 1):
            print(f"{index}. {course.get('courseId','')} - {course.get('courseTitle','')} (Section: {course.get('section','')})")
    except Exception as error:
        print(f"Error parsing HTML: {error}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
