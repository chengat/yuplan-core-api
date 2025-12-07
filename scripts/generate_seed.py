import json
import uuid
from collections import defaultdict
from typing import Dict, List, Tuple, Set
from urllib.parse import quote_plus

def escape_sql_string(s: str) -> str:
    """Escape single quotes for SQL"""
    if s is None:
        return 'NULL'
    return "'" + s.replace("'", "''") + "'"

def format_schedule(schedule: List[Dict]) -> str:
    """Format schedule array as JSON string for persistence"""
    if not schedule:
        return 'NULL'

    json_str = json.dumps(schedule)
    return escape_sql_string(json_str)

def parse_instructor_name(name: str) -> Tuple[str, str]:
    """Transform instructor full name into first_name and last_name"""
    if not name or not name.strip():
        return ('', '')
    
    parts = name.strip().split()
    if len(parts) == 1:
        return (parts[0], '')
    elif len(parts) == 2:
        return (parts[0], parts[1])
    else:
        # Multiple parts, assuming last is last_name, rest is first_name
        return (' '.join(parts[:-1]), parts[-1])

def generate_rate_my_prof_url(first_name: str, last_name: str) -> str:
    """Generating Rate My Professor search URL for an instructor"""
    if not first_name and not last_name:
        return None
    
    full_name = f"{first_name} {last_name}".strip()
    if not full_name:
        return None
    
    # encode the name
    encoded_name = quote_plus(full_name)
    return f"https://www.ratemyprofessors.com/search/professors/?q={encoded_name}"

def collect_courses_and_instructors(courses: List[Dict]) -> Tuple[Dict[str, Tuple[str, str]], List[Dict], Dict[str, str], Dict[str, int]]:
    """Collect unique courses and all instructors"""
    instructors_map: Dict[str, Tuple[str, str]] = {}
    courses_list: List[Dict] = []
    course_code_to_uuid: Dict[str, str] = {}
    course_code_to_index: Dict[str, int] = {}
    
    for course in courses:
        course_title = course.get('courseTitle', '')
        department = course.get('department', '')
        course_id = course.get('courseId', '')
        course_code = f"{department}{course_id}"
        
        # Only create course if does not exist yet
        if course_code not in course_code_to_uuid:
            credits = float(course.get('credits', '0.00'))
            description = course.get('notes', '')
            
            course_uuid = str(uuid.uuid4())
            course_code_to_uuid[course_code] = course_uuid
            course_index = len(courses_list)
            course_code_to_index[course_code] = course_index
            
            courses_list.append({
                'code': course_code,
                'name': course_title,
                'credits': credits,
                'description': description,
                'uuid': course_uuid
            })
        
        # Collect instructors from all sections (even if course already exists)
        for section in course.get('sections', []):
            for instructor_name in section.get('instructors', []):
                if instructor_name and instructor_name.strip():
                    instructors_map[instructor_name.strip()] = parse_instructor_name(instructor_name)
    
    return instructors_map, courses_list, course_code_to_uuid, course_code_to_index

def process_sections(courses: List[Dict], course_code_to_index: Dict[str, int]) -> Tuple[List[Dict], List[Dict], List[Dict], List[Tuple[str, str]]]:
    """Process sections into labs, tutorials, sections, and instructor-course links"""
    labs_list: List[Dict] = []
    tutorials_list: List[Dict] = []
    sections_list: List[Dict] = []
    instructor_course_links: List[Tuple[str, str]] = []
    
    for course in courses:
        course_code = f"{course.get('department', '')}{course.get('courseId', '')}"
        course_idx = course_code_to_index.get(course_code)
        if course_idx is None:
            continue
        
        for section in course.get('sections', []):
            lab_entry, tutorial_entry, section_entry, instructor_links = process_single_section(
                section, course_idx, course_code
            )
            
            if lab_entry:
                labs_list.append(lab_entry)
            if tutorial_entry:
                tutorials_list.append(tutorial_entry)
            if section_entry:
                sections_list.append(section_entry)
            
            instructor_course_links.extend(instructor_links)
    
    return labs_list, tutorials_list, sections_list, instructor_course_links

def process_single_section(section: Dict, course_idx: int, course_code: str) -> Tuple[Dict, Dict, Dict, List[Tuple[str, str]]]:
    """Process a single section"""
    section_type = section.get('type', '').upper()
    catalog_number = section.get('catalogNumber', '')
    schedule = section.get('schedule', [])
    meet_number = section.get('meetNumber', '01')
    instructors = section.get('instructors', [])
    
    times_str = format_schedule(schedule)
    lab_entry = None
    tutorial_entry = None
    section_entry = None
    
    if section_type == 'LAB':
        lab_entry = {
            'course_idx': course_idx,
            'catalog_number': catalog_number,
            'times': times_str
        }
    elif section_type in ['TUT', 'TUTR']:
        tutorial_entry = {
            'course_idx': course_idx,
            'catalog_number': catalog_number,
            'times': times_str
        }
    elif section_type in ['LECT', 'ONLN']:
        section_entry = {
            'course_idx': course_idx,
            'lab_id': None,
            'letter': meet_number
        }
    
    # Extract instructor-course links
    instructor_links = []
    for instructor_name in instructors:
        if instructor_name and instructor_name.strip():
            instructor_links.append((instructor_name.strip(), course_code))
    
    return lab_entry, tutorial_entry, section_entry, instructor_links

def generate_instructor_sql(instructors_map: Dict[str, Tuple[str, str]]) -> Tuple[List[str], Dict[str, str]]:
    """Generate SQL INSERT statements for instructors"""
    sql_lines = ["-- Insert instructors"]
    instructor_inserts = []
    instructor_name_to_uuid: Dict[str, str] = {}
    
    for name, (first, last) in sorted(instructors_map.items()):
        instructor_uuid = str(uuid.uuid4())
        instructor_name_to_uuid[name] = instructor_uuid
        first_escaped = escape_sql_string(first) if first else 'NULL'
        last_escaped = escape_sql_string(last) if last else 'NULL'
        rmp_url = generate_rate_my_prof_url(first, last)
        rmp_url_escaped = escape_sql_string(rmp_url) if rmp_url else 'NULL'
        instructor_inserts.append(f"('{instructor_uuid}', {first_escaped}, {last_escaped}, {rmp_url_escaped})")
    
    if instructor_inserts:
        sql_lines.append("INSERT INTO instructors (id, first_name, last_name, rate_my_prof_link) VALUES")
        sql_lines.append(",\n".join(instructor_inserts) + ";")
        sql_lines.append("")
    
    return sql_lines, instructor_name_to_uuid

def generate_course_sql(courses_list: List[Dict]) -> List[str]:
    """Generate SQL INSERT statements for courses"""
    sql_lines = ["-- Insert courses"]
    course_inserts = []
    
    for course in courses_list:
        course_uuid = course['uuid']
        code = escape_sql_string(course['code'])
        name = escape_sql_string(course['name'])
        credits = course['credits']
        description = escape_sql_string(course['description']) if course['description'] else 'NULL'
        course_inserts.append(f"('{course_uuid}', {name}, {code}, {credits}, {description})")
    
    if course_inserts:
        sql_lines.append("INSERT INTO courses (id, name, code, credits, description) VALUES")
        sql_lines.append(",\n".join(course_inserts) + ";")
        sql_lines.append("")
    
    return sql_lines

def generate_lab_sql(labs_list: List[Dict], courses_list: List[Dict]) -> List[str]:
    """Generate SQL INSERT statements for labs"""
    sql_lines = ["-- Insert labs"]
    
    if not labs_list:
        return sql_lines
    
    lab_inserts = []
    for lab in labs_list:
        lab_uuid = str(uuid.uuid4())
        course_idx = lab['course_idx']
        course_uuid = courses_list[course_idx]['uuid']
        catalog_number = escape_sql_string(lab['catalog_number'])
        times = lab['times']
        lab_inserts.append(f"('{lab_uuid}', '{course_uuid}', {catalog_number}, {times})")
    
    sql_lines.append("INSERT INTO labs (id, course_id, catalog_number, times) VALUES")
    sql_lines.append(",\n".join(lab_inserts) + ";")
    sql_lines.append("")
    
    return sql_lines

def generate_tutorial_sql(tutorials_list: List[Dict], courses_list: List[Dict]) -> List[str]:
    """Generate SQL INSERT statements for tutorials"""
    sql_lines = ["-- Insert tutorials"]
    
    if not tutorials_list:
        return sql_lines
    
    tutorial_inserts = []
    for tut in tutorials_list:
        tut_uuid = str(uuid.uuid4())
        course_idx = tut['course_idx']
        course_uuid = courses_list[course_idx]['uuid']
        catalog_number = escape_sql_string(tut['catalog_number'])
        times = tut['times']
        tutorial_inserts.append(f"('{tut_uuid}', '{course_uuid}', {catalog_number}, {times})")
    
    sql_lines.append("INSERT INTO tutorials (id, course_id, catalog_number, times) VALUES")
    sql_lines.append(",\n".join(tutorial_inserts) + ";")
    sql_lines.append("")
    
    return sql_lines

def generate_section_sql(sections_list: List[Dict], courses_list: List[Dict]) -> List[str]:
    """Generate SQL INSERT statements for sections"""
    sql_lines = ["-- Insert sections"]
    
    if not sections_list:
        return sql_lines
    
    section_inserts = []
    for section in sections_list:
        section_uuid = str(uuid.uuid4())
        course_idx = section['course_idx']
        course_uuid = courses_list[course_idx]['uuid']
        lab_id = 'NULL'
        letter = escape_sql_string(section['letter'])
        section_inserts.append(f"('{section_uuid}', '{course_uuid}', {lab_id}, {letter})")
    
    sql_lines.append("INSERT INTO sections (id, course_id, lab_id, letter) VALUES")
    sql_lines.append(",\n".join(section_inserts) + ";")
    sql_lines.append("")
    
    return sql_lines

def generate_junction_table_sql(instructor_course_links: List[Tuple[str, str]], 
                                instructor_name_to_uuid: Dict[str, str],
                                course_code_to_uuid: Dict[str, str]) -> List[str]:
    """Generate SQL INSERT statements for instructor_courses junction table"""
    sql_lines = ["-- Insert instructor_courses junction table"]
    
    if not instructor_course_links:
        return sql_lines
    
    unique_links = set(instructor_course_links)
    junction_inserts = []
    for instructor_name, course_code in unique_links:
        instructor_uuid = instructor_name_to_uuid.get(instructor_name)
        course_uuid = course_code_to_uuid.get(course_code)
        if instructor_uuid and course_uuid:
            junction_inserts.append(f"('{instructor_uuid}', '{course_uuid}')")
    
    if junction_inserts:
        sql_lines.append("INSERT INTO instructor_courses (instructor_id, course_id) VALUES")
        sql_lines.append(",\n".join(junction_inserts) + ";")
        sql_lines.append("")
    
    return sql_lines

def generate_seed_sql(json_file: str, output_file: str):
    """Generate seed.sql from lassonde.json"""
    
    # Read JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    courses = data.get('courses', [])
    
    # Collect data from JSON
    instructors_map, courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors(courses)
    labs_list, tutorials_list, sections_list, instructor_course_links = process_sections(courses, course_code_to_index)
    
    # Generate SQL statements
    sql_lines = [
        "-- Generated seed file from JSON data",
        "-- This file is auto-generated. Do not edit manually.",
        "",
        "BEGIN;",
        ""
    ]
    
    # Generate SQL for each table
    instructor_sql, instructor_name_to_uuid = generate_instructor_sql(instructors_map)
    sql_lines.extend(instructor_sql)
    
    sql_lines.extend(generate_course_sql(courses_list))
    sql_lines.extend(generate_lab_sql(labs_list, courses_list))
    sql_lines.extend(generate_tutorial_sql(tutorials_list, courses_list))
    sql_lines.extend(generate_section_sql(sections_list, courses_list))
    sql_lines.extend(generate_junction_table_sql(instructor_course_links, instructor_name_to_uuid, course_code_to_uuid))
    
    sql_lines.append("COMMIT;")
    sql_lines.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f" Generated {output_file}")
    print(f"   - {len(instructors_map)} instructors")
    print(f"   - {len(courses_list)} courses")
    print(f"   - {len(labs_list)} labs")
    print(f"   - {len(tutorials_list)} tutorials")
    print(f"   - {len(sections_list)} sections")

if __name__ == '__main__':
    import sys
    
    json_file = 'scraping/data/lassonde.json'
    output_file = 'db/seed.sql'
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    generate_seed_sql(json_file, output_file)

