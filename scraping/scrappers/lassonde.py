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

    # A header row has 4 bodytext TDs and the 4th has colspan
    def is_header_row(table_row) -> bool:
        bodytext_cells = table_row.find_all("td", class_="bodytext", recursive=False)
        return len(bodytext_cells) >= 4 and bodytext_cells[3].has_attr("colspan")

    courses: List[Dict[str, Any]] = []
    
    # Collect all header rows across the table (handles imperfect HTML nesting)
    header_rows = [tr for tr in table.find_all("tr") if is_header_row(tr)]

    for header in header_rows:
        header_cells = header.find_all("td", class_="bodytext", recursive=False)
        course: Dict[str, Any] = {
            "faculty": cell_text(header_cells[0]),
            "department": cell_text(header_cells[1]),
            "term": cell_text(header_cells[2]),
            "courseTitle": cell_text(header_cells[3]),
            "courseId": "",
            "credits": "",
            "section": "",
            "languageOfInstruction": "",
            "sections": [],
        }
        allowed_section_types = ["LECT", "SEMR", "ONLN", "BLEN", "COOP", "ISTY"]

        # Walk forward in document order until the next header row.
        # This tolerates malformed HTML where section rows aren't proper siblings.
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

            section_type_index = None
            for index, cell in enumerate(row_cells):
                if get_section_type(cell_text(cell)):
                    section_type_index = index
                    break
            if section_type_index is None:
                continue

            # Capture summary and LOI if present to the left of type
            if not course["courseId"] or not course["credits"] or not course["section"]:
                summary_pattern = re.compile(r"(\d{3,4})\s+([0-9]+\.[0-9]{2})\s*([A-Z0-9]?)")
                for cell_index in range(section_type_index - 1, -1, -1):
                    match = summary_pattern.search(cell_text(row_cells[cell_index]))
                    if match:
                        course_id, credits, section_letter = match.group(1), match.group(2), match.group(3)
                        if course_id and not course["courseId"]:
                            course["courseId"] = course_id
                        if credits and not course["credits"]:
                            course["credits"] = credits
                        if section_letter and not course["section"]:
                            course["section"] = section_letter
                        break

            if not course["languageOfInstruction"]:
                for cell_index in range(section_type_index - 1, -1, -1):
                    token = cell_text(row_cells[cell_index])
                    if 1 < len(token) <= 3 and token.isupper() and token.isalpha():
                        course["languageOfInstruction"] = token
                        break

            section_type = get_section_type(cell_text(row_cells[section_type_index]))
            # Build a detail object for the current row
            def build_detail():
                schedule: List[Dict[str, str]] = []
                catalog_cell = row_cells[section_type_index + 2] if len(row_cells) > section_type_index + 2 else None
                schedule_cell = row_cells[section_type_index + 3] if len(row_cells) > section_type_index + 3 else None
                instructors: List[str] = []
                notes = ""
                
                catalog_num = cell_text(catalog_cell) if catalog_cell else ""
                is_cancelled = catalog_num.lower() == "cancelled"
                
                if schedule_cell is not None:
                    inner_table = schedule_cell.find("table")
                    if inner_table:
                        for schedule_row in inner_table.find_all("tr"):
                            schedule_cells = schedule_row.find_all("td")
                            if len(schedule_cells) >= 5:
                                entry = {
                                    "day": cell_text(schedule_cells[0]),
                                    "time": cell_text(schedule_cells[1]),
                                    "duration": cell_text(schedule_cells[2]),
                                    "campus": cell_text(schedule_cells[3]),
                                    "room": clean_room(cell_text(schedule_cells[4])),
                                }
                                if any(entry.values()):
                                    schedule.append(entry)
                    else:
                        schedule_text = cell_text(schedule_cell)
                        if schedule_text and schedule_text.lower() != "cancelled":
                            schedule.append({"day": "", "time": schedule_text, "duration": "", "campus": "", "room": ""})
                    
                    # Due to malformed HTML, instructor and notes TDs are nested inside schedule_cell
                    nested_tds = schedule_cell.find_all("td", recursive=False)
                    if len(nested_tds) >= 1:
                        instructors = parse_instructors(nested_tds[0].decode_contents())
                    if len(nested_tds) >= 2:
                        notes = parse_notes(nested_tds[1].decode_contents())
                
                # For cancelled entries, notes may be in a separate TD after schedule_cell
                # The HTML has malformed structure where instructor and notes TDs may be siblings
                if is_cancelled and not notes:
                    # Try multiple positions as the HTML structure varies
                    for offset in [4, 5]:
                        if len(row_cells) > section_type_index + offset:
                            potential_notes = parse_notes(row_cells[section_type_index + offset].decode_contents())
                            if potential_notes and potential_notes.strip():
                                notes = potential_notes
                                break

                return schedule, instructors, notes

            # All section types go into sections array
            schedule, instructors, notes = build_detail()
            section_detail = {
                "type": section_type,
                "meetNumber": cell_text(row_cells[section_type_index + 1]) if len(row_cells) > section_type_index + 1 else "",
                "catalogNumber": cell_text(row_cells[section_type_index + 2]) if len(row_cells) > section_type_index + 2 else "",
                "schedule": schedule,
                "instructors": instructors,
                "notes": notes,
            }
            if section_type or section_detail["meetNumber"] or section_detail["catalogNumber"] or section_detail["schedule"] or section_detail["instructors"] or section_detail["notes"]:
                course["sections"].append(section_detail)

        courses.append(course)

    return {
        "metadata": {"title": title, "lastUpdated": last_updated, "source": "York University"},
        "courses": courses,
    }


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
