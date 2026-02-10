"""Glendon course timetable scraper."""

import json
from pathlib import Path

from helpers.parser import parse_course_timetable_html


def main():
    scraping_dir = Path(__file__).resolve().parents[1]
    html_path = scraping_dir / "page_source" / "glendon.html"
    data_path = scraping_dir / "data" / "glendon.json"

    try:
        html_content = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception as error:
        print(f"Error reading HTML: {error}")
        return

    try:
        result = parse_course_timetable_html(html_content, extract_metadata=True)
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved: {data_path}")
        print(f"Courses: {len(result.get('courses', []))}")
        for index, course in enumerate(result.get('courses', []), 1):
            section_letters = sorted({section.get('section', '') for section in course.get('sections', []) if section.get('section')})
            section_display = ",".join(section_letters)
            print(f"{index}. {course.get('courseId','')} - {course.get('courseTitle','')} (Section: {section_display})")
    except Exception as error:
        print(f"Error parsing HTML: {error}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
