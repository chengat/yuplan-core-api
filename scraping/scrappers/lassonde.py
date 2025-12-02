import json
import re
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any
import html
from pathlib import Path


def norm_text(s: str) -> str:
    if s is None:
        return ""
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def cell_text(el) -> str:
    if el is None:
        return ""
    txt = el.get_text(" ", strip=True)
    txt = txt.replace("\xa0", " ")
    return norm_text(txt)


def get_section_type(text: str) -> str:
    t = norm_text(text).upper()
    t_compact = re.sub(r"[^A-Z]", "", t)
    mappings = [
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
    for pat, norm in mappings:
        if pat in t_compact:
            return norm
    return ""


def parse_instructors(instructor_html: str) -> List[str]:
    if not instructor_html:
        return []
    text = re.sub(r"<br\s*/?>", "|", instructor_html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    parts = re.split(r"[|,;&]", text)
    out: List[str] = []
    for p in parts:
        name = norm_text(p)
        if name and name.lower() not in {"nbsp", "amp", "lt", "gt"}:
            out.append(name)
    return out


def parse_notes(notes_html: str) -> str:
    if not notes_html:
        return ""
    s = re.sub(r"<br\s*/?>", " | ", notes_html, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" |")


def clean_room(room_text: str) -> str:
    s = norm_text(room_text)
    return s


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
    def is_header_row(tr) -> bool:
        tds_body = tr.find_all("td", class_="bodytext", recursive=False)
        return len(tds_body) >= 4 and tds_body[3].has_attr("colspan")

    courses: List[Dict[str, Any]] = []
    
    # Collect all header rows across the table (handles imperfect HTML nesting)
    header_rows = [tr for tr in table.find_all("tr") if is_header_row(tr)]

    for header in header_rows:
        header_tds = header.find_all("td", class_="bodytext", recursive=False)
        course: Dict[str, Any] = {
            "faculty": cell_text(header_tds[0]),
            "department": cell_text(header_tds[1]),
            "term": cell_text(header_tds[2]),
            "courseTitle": cell_text(header_tds[3]),
            "courseId": "",
            "credits": "",
            "section": "",
            "languageOfInstruction": "",
            "sections": [],
        }
        allowed_section_types = ["LECT", "SEMR", "ONLN", "BLEN", "COOP", "ISTY"]

        # Walk forward in document order until the next header row.
        # This tolerates malformed HTML where section rows aren't proper siblings.
        for el in header.next_elements:
            if not isinstance(el, Tag):
                continue
            if el is header:
                continue
            if el.name != "tr":
                continue
            if is_header_row(el):
                break

            tds = el.find_all("td", recursive=False)
            if not tds:
                continue

            type_idx = None
            for idx, td in enumerate(tds):
                if get_section_type(cell_text(td)):
                    type_idx = idx
                    break
            if type_idx is None:
                continue

            # Capture summary and LOI if present to the left of type
            if not course["courseId"] or not course["credits"] or not course["section"]:
                summary_re = re.compile(r"(\d{3,4})\s+([0-9]+\.[0-9]{2})\s*([A-Z0-9]?)")
                for j in range(type_idx - 1, -1, -1):
                    m = summary_re.search(cell_text(tds[j]))
                    if m:
                        cid, credits, mode = m.group(1), m.group(2), m.group(3)
                        if cid and not course["courseId"]:
                            course["courseId"] = cid
                        if credits and not course["credits"]:
                            course["credits"] = credits
                        if mode and not course["section"]:
                            course["section"] = mode
                        break

            if not course["languageOfInstruction"]:
                for j in range(type_idx - 1, -1, -1):
                    tok = cell_text(tds[j])
                    if 1 < len(tok) <= 3 and tok.isupper() and tok.isalpha():
                        course["languageOfInstruction"] = tok
                        break

            section_type = get_section_type(cell_text(tds[type_idx]))
            # Build a detail object for the current row
            def build_detail():
                schedule: List[Dict[str, str]] = []
                catalog_cell = tds[type_idx + 2] if len(tds) > type_idx + 2 else None
                schedule_cell = tds[type_idx + 3] if len(tds) > type_idx + 3 else None
                instructors: List[str] = []
                notes = ""
                
                catalog_num = cell_text(catalog_cell) if catalog_cell else ""
                is_cancelled = catalog_num.lower() == "cancelled"
                
                if schedule_cell is not None:
                    inner = schedule_cell.find("table")
                    if inner:
                        for s_tr in inner.find_all("tr"):
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
                        txt = cell_text(schedule_cell)
                        if txt and txt.lower() != "cancelled":
                            schedule.append({"day": "", "time": txt, "duration": "", "campus": "", "room": ""})
                    
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
                        if len(tds) > type_idx + offset:
                            potential_notes = parse_notes(tds[type_idx + offset].decode_contents())
                            if potential_notes and potential_notes.strip():
                                notes = potential_notes
                                break

                return schedule, instructors, notes

            # All section types go into sections array
            schedule, instructors, notes = build_detail()
            detail = {
                "type": section_type,
                "meetNumber": cell_text(tds[type_idx + 1]) if len(tds) > type_idx + 1 else "",
                "catalogNumber": cell_text(tds[type_idx + 2]) if len(tds) > type_idx + 2 else "",
                "schedule": schedule,
                "instructors": instructors,
                "notes": notes,
            }
            if section_type or detail["meetNumber"] or detail["catalogNumber"] or detail["schedule"] or detail["instructors"] or detail["notes"]:
                course["sections"].append(detail)

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
    except Exception as e:
        print(f"Error reading HTML: {e}")
        return

    try:
        result = parse_course_timetable_html(html_content)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved: {data_path}")
        print(f"Courses: {len(result.get('courses', []))}")
        for i, c in enumerate(result.get('courses', []), 1):
            print(f"{i}. {c.get('courseId','')} - {c.get('courseTitle','')} (Section: {c.get('section','')})")
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
