import json
import uuid
from collections import defaultdict
from pathlib import Path
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

def load_course_descriptions(descriptions_file: str) -> Dict[str, str]:
    """Load course descriptions from JSON file and create a mapping of code to description"""
    descriptions_map = {}
    try:
        with open(descriptions_file, 'r', encoding='utf-8') as f:
            descriptions_data = json.load(f)
        
        for item in descriptions_data:
            code = item.get('course_code', '')
            description = item.get('description', '')
            if code and description:
                descriptions_map[code] = description
        
        print(f"Loaded {len(descriptions_map)} course descriptions from {descriptions_file}")
    except FileNotFoundError:
        print(f"Warning: Course descriptions file not found: {descriptions_file}")
    except Exception as e:
        print(f"Warning: Error loading course descriptions: {e}")
    
    return descriptions_map

def collect_courses_and_instructors(courses: List[Dict], descriptions_map: Dict[str, str] = None) -> Tuple[List[Dict], Dict[str, str], Dict[str, int]]:
    """Collect unique courses (unique by code + term combination)"""
    courses_list: List[Dict] = []
    course_code_to_uuid: Dict[str, str] = {}
    course_code_to_index: Dict[str, int] = {}
    
    for course in courses:
        course_title = course.get('courseTitle', '')
        department = course.get('department', '')
        course_id = course.get('courseId', '')
        course_code = f"{department}{course_id}"
        term = course.get('term', '')
        faculty = course.get('faculty', '')
        
        # Make courses unique by code + term combination
        course_key = f"{course_code}_{term}"
        
        # Only create course if does not exist yet
        if course_key not in course_code_to_uuid:
            credits_str = course.get('credits', '0.00')
            # Handle empty strings or invalid credit values
            try:
                credits = float(credits_str) if credits_str else 0.0
            except (ValueError, TypeError):
                credits = 0.0
            
            # Get description from descriptions_map if available, otherwise use notes field
            description = ''
            if descriptions_map:
                description = descriptions_map.get(course_code, '')
            if not description:
                description = course.get('notes', '')
            
            course_uuid = str(uuid.uuid4())
            course_code_to_uuid[course_key] = course_uuid
            course_index = len(courses_list)
            course_code_to_index[course_key] = course_index
            
            courses_list.append({
                'code': course_code,
                'name': course_title,
                'credits': credits,
                'description': description,
                'faculty': faculty,
                'term': term,
                'uuid': course_uuid
            })
    
    return courses_list, course_code_to_uuid, course_code_to_index

def process_sections(courses: List[Dict], course_code_to_index: Dict[str, int]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Process sections into section_activities, sections, and instructors with section associations
    
    Strategy:
    1. First pass: Identify all unique section letters for each course (regardless of activity type)
    2. Create a section record for each unique section letter
    3. Second pass: Put ALL activity types (LECT, BLEN, LAB, TUT, etc.) into section_activities
       with their catalog_numbers (catalog_number is always associated with a course_type)
    
    This ensures:
    - Every course always has at least one section record
    - All activity types are stored consistently in section_activities
    - Catalog numbers are stored with their corresponding course_type in section_activities
    - Querying by section_id returns all activities for that section
    """
    section_activities_list: List[Dict] = []
    sections_list: List[Dict] = []
    instructors_list: List[Dict] = []
    
    for course in courses:
        course_code = f"{course.get('department', '')}{course.get('courseId', '')}"
        term = course.get('term', '')
        course_key = f"{course_code}_{term}"
        course_idx = course_code_to_index.get(course_key)
        if course_idx is None:
            continue
        
        # First pass: Collect all unique section letters and create section records
        # Only create sections from entries that have a 'section' field (actual section letters like A, B, C)
        section_uuid_map: Dict[Tuple[int, str], str] = {}
        
        for section in course.get('sections', []):
            section_letter = section.get('section')
            # Only create section records for entries that have an actual section letter
            if section_letter:
                section_key = (course_idx, section_letter)
                
                # Create section record if we haven't seen this section letter yet
                if section_key not in section_uuid_map:
                    section_uuid = str(uuid.uuid4())
                    section_uuid_map[section_key] = section_uuid
                    sections_list.append({
                        'uuid': section_uuid,
                        'course_idx': course_idx,
                        'letter': section_letter
                    })
        
        # Second pass: Process all sections and create activities/instructors
        # For entries without a 'section' field, associate with the most recent section
        current_section_uuid = None
        
        for section in course.get('sections', []):
            section_type = section.get('type', '').upper()
            section_letter = section.get('section')
            
            # If this entry has a section letter, use it
            if section_letter:
                section_key = (course_idx, section_letter)
                section_uuid = section_uuid_map.get(section_key)
                if section_uuid:
                    current_section_uuid = section_uuid
            # If no section letter, use the most recent section (or first if none yet)
            elif current_section_uuid is None:
                # Find first section for this course
                for (c_idx, letter), sec_uuid in section_uuid_map.items():
                    if c_idx == course_idx:
                        current_section_uuid = sec_uuid
                        break
            
            # Skip if we still don't have a section to associate with
            if not current_section_uuid:
                continue
            
            # Extract catalog_number and times (catalog_number is always associated with course_type)
            catalog_number = section.get('catalogNumber', '')
            schedule = section.get('schedule', [])
            times_str = format_schedule(schedule)
            
            # ALL activity types go into section_activities (including LECT, BLEN, etc.)
            activity_entry = {
                'section_uuid': current_section_uuid,
                'course_type': section_type,
                'catalog_number': catalog_number,
                'times': times_str
            }
            section_activities_list.append(activity_entry)
            
            # Process instructors (typically associated with LECT/BLEN but can be any type)
            instructors = section.get('instructors', [])
            for instructor_name in instructors:
                if instructor_name and instructor_name.strip():
                    instructors_list.append({
                        'name': instructor_name.strip(),
                        'section_uuid': current_section_uuid
                    })
    
    return section_activities_list, sections_list, instructors_list


def generate_instructor_sql(instructors_list: List[Dict]) -> List[str]:
    """Generate SQL INSERT statements for instructors with section_id"""
    sql_lines = ["-- Insert instructors"]
    
    if not instructors_list:
        return sql_lines
    
    # Each instructor-section combination gets its own record
    instructor_inserts = []
    for inst in instructors_list:
        name = inst['name']
        section_uuid = inst['section_uuid']
        first, last = parse_instructor_name(name)
        instructor_uuid = str(uuid.uuid4())
        first_escaped = escape_sql_string(first) if first else 'NULL'
        last_escaped = escape_sql_string(last) if last else 'NULL'
        rmp_url = generate_rate_my_prof_url(first, last)
        rmp_url_escaped = escape_sql_string(rmp_url) if rmp_url else 'NULL'
        instructor_inserts.append(f"('{instructor_uuid}', {first_escaped}, {last_escaped}, {rmp_url_escaped}, '{section_uuid}')")
    
    sql_lines.append("INSERT INTO instructors (id, first_name, last_name, rate_my_prof_link, section_id) VALUES")
    sql_lines.append(",\n".join(instructor_inserts) + ";")
    sql_lines.append("")
    
    return sql_lines

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
        faculty = escape_sql_string(course.get('faculty', '')) if course.get('faculty') else 'NULL'
        term = escape_sql_string(course.get('term', '')) if course.get('term') else 'NULL'
        course_inserts.append(f"('{course_uuid}', {name}, {code}, {credits}, {description}, {faculty}, {term})")
    
    if course_inserts:
        sql_lines.append("INSERT INTO courses (id, name, code, credits, description, faculty, term) VALUES")
        sql_lines.append(",\n".join(course_inserts) + ";")
        sql_lines.append("")
    
    return sql_lines

def generate_section_activity_sql(activities_list: List[Dict]) -> List[str]:
    """Generate SQL INSERT statements for section_activities with section_id"""
    sql_lines = ["-- Insert section activities"]
    
    if not activities_list:
        return sql_lines
    
    activity_inserts = []
    for activity in activities_list:
        activity_uuid = str(uuid.uuid4())
        section_uuid = activity['section_uuid']
        course_type = escape_sql_string(activity['course_type'])
        catalog_number = escape_sql_string(activity['catalog_number'])
        times = activity['times']
        activity_inserts.append(f"('{activity_uuid}', {course_type}, '{section_uuid}', {catalog_number}, {times})")
    
    sql_lines.append("INSERT INTO section_activities (id, course_type, section_id, catalog_number, times) VALUES")
    sql_lines.append(",\n".join(activity_inserts) + ";")
    sql_lines.append("")
    
    return sql_lines

def generate_section_sql(sections_list: List[Dict], courses_list: List[Dict]) -> List[str]:
    """Generate SQL INSERT statements for sections"""
    sql_lines = ["-- Insert sections"]
    
    if not sections_list:
        return sql_lines
    
    section_inserts = []
    for section in sections_list:
        section_uuid = section['uuid']
        course_idx = section['course_idx']
        course_uuid = courses_list[course_idx]['uuid']
        letter = escape_sql_string(section['letter'])
        section_inserts.append(f"('{section_uuid}', '{course_uuid}', {letter})")
    
    sql_lines.append("INSERT INTO sections (id, course_id, letter) VALUES")
    sql_lines.append(",\n".join(section_inserts) + ";")
    sql_lines.append("")
    
    return sql_lines

def generate_seed_sql(json_files: list[str], output_file: str, descriptions_file: str = None):
    """Generate seed.sql for all generated JSON data"""

    # Load course descriptions if file is provided
    descriptions_map = {}
    if descriptions_file:
        descriptions_map = load_course_descriptions(descriptions_file)

    # Initialize collections
    all_courses_list = []
    all_course_code_to_uuid = {}
    all_course_code_to_index = {}
    all_section_activities_list = []
    all_sections_list = []
    all_instructors_list = []
    
    # Process each JSON file
    for json_file in json_files:
        print(f"Processing {json_file}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        courses = data.get('courses', [])
        
        # Collect data from JSON
        courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors(courses, descriptions_map)
        activities_list, sections_list, instructors_list = process_sections(courses, course_code_to_index)
        
        # Adjust course indices to avoid collisions
        offset = len(all_courses_list)
        for course in courses_list:
            all_courses_list.append(course)
        
        # Update course mappings with offset
        for code, uuid_val in course_code_to_uuid.items():
            all_course_code_to_uuid[code] = uuid_val
        
        for code, idx in course_code_to_index.items():
            all_course_code_to_index[code] = idx + offset
        
        # Adjust course indices in sections and merge
        for section in sections_list:
            section['course_idx'] = section['course_idx'] + offset
            all_sections_list.append(section)
        
        # Merge section activities (they reference sections by UUID, so no offset needed)
        all_section_activities_list.extend(activities_list)
        
        # Merge instructors (they reference sections by UUID, so no offset needed)
        all_instructors_list.extend(instructors_list)
    
    # Generate SQL statements
    sql_lines = [
        "-- Generated seed file from JSON data",
        "-- This file is auto-generated. Do not edit manually.",
        "",
        "BEGIN;",
        ""
    ]
    
    # Generate SQL for each table - order matters: courses -> sections -> section_activities/instructors
    sql_lines.extend(generate_course_sql(all_courses_list))
    sql_lines.extend(generate_section_sql(all_sections_list, all_courses_list))
    sql_lines.extend(generate_section_activity_sql(all_section_activities_list))
    sql_lines.extend(generate_instructor_sql(all_instructors_list))
    
    sql_lines.append("COMMIT;")
    sql_lines.append("")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"\n✓ Generated {output_file}")
    print(f"   - {len(all_instructors_list)} instructors")
    print(f"   - {len(all_courses_list)} courses")
    print(f"   - {len(all_section_activities_list)} section activities")
    print(f"   - {len(all_sections_list)} sections")

if __name__ == '__main__':
    import sys
    import os
    import glob
    
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = str(repo_root / 'scraping' / 'data')
    output_file = str(repo_root / 'db' / 'seed.sql')
    descriptions_file = str(repo_root / 'scraping' / 'scrapers' / 'descriptions' / 'course_descriptions.json')
    
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        descriptions_file = sys.argv[3]

    json_files = glob.glob(os.path.join(data_dir, '*', '*.json'))

    if not json_files:
        print(f"No JSON files found in {data_dir}")
        sys.exit(1)

    print(f"Found {len(json_files)} JSON file(s) to process:")  # Fixed!
    for json_file in json_files:
        print(f"  - {json_file}")
    
    generate_seed_sql(json_files, output_file, descriptions_file)
