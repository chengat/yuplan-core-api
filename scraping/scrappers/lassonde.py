import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import html

def parse_instructors(instructor_text: str) -> List[str]:
    """
    Parse instructor text and return a list of instructors.
    Handles cases with <br> tags and other separators.
    """
    if not instructor_text or instructor_text.strip() == "":
        return []
    
    # Replace <br> tags with a delimiter
    instructor_text = re.sub(r'<br\s*/?>', '|', instructor_text, flags=re.IGNORECASE)
    
    # Split by common delimiters and clean up
    instructors = re.split(r'[|,;&]', instructor_text)
    
    # Clean up each instructor name
    cleaned_instructors = []
    for instructor in instructors:
        # Remove HTML tags
        clean_instructor = re.sub(r'<[^>]+>', '', instructor)
        
        # Decode HTML entities (like &nbsp;, &amp;, etc.)
        clean_instructor = html.unescape(clean_instructor)
        
        # Remove common HTML entities that might not be decoded
        clean_instructor = re.sub(r'&nbsp;?', '', clean_instructor, flags=re.IGNORECASE)
        clean_instructor = re.sub(r'&amp;?', '', clean_instructor, flags=re.IGNORECASE)
        clean_instructor = re.sub(r'&lt;?', '', clean_instructor, flags=re.IGNORECASE)
        clean_instructor = re.sub(r'&gt;?', '', clean_instructor, flags=re.IGNORECASE)
        
        # Remove extra whitespace and normalize
        clean_instructor = re.sub(r'\s+', ' ', clean_instructor).strip()
        
        # Only add if it's not empty and not just "nbsp" or similar artifacts
        if clean_instructor and clean_instructor.lower() not in ['nbsp', 'amp', 'lt', 'gt', '&', '<', '>']:
            cleaned_instructors.append(clean_instructor)
    
    return cleaned_instructors

def clean_room(room_text: str) -> str:
    """
    Clean room text by removing HTML entities and extra whitespace.
    Returns empty string if room is just nbsp or similar artifacts.
    """
    if not room_text:
        return ""
    
    # Decode HTML entities
    clean_room = html.unescape(room_text)
    
    # Remove common HTML entities that might not be decoded
    clean_room = re.sub(r'&nbsp;?', '', clean_room, flags=re.IGNORECASE)
    clean_room = re.sub(r'&amp;?', '', clean_room, flags=re.IGNORECASE)
    clean_room = re.sub(r'&lt;?', '', clean_room, flags=re.IGNORECASE)
    clean_room = re.sub(r'&gt;?', '', clean_room, flags=re.IGNORECASE)
    
    # Remove HTML tags
    clean_room = re.sub(r'<[^>]+>', '', clean_room)
    
    # Normalize whitespace
    clean_room = re.sub(r'\s+', ' ', clean_room).strip()
    
    # Return empty string if it's just artifacts or meaningless content
    if clean_room.lower() in ['nbsp', 'amp', 'lt', 'gt', '&', '<', '>', '']:
        return ""
    
    return clean_room

def parse_notes(notes_text: str) -> str:
    """
    Parse and clean notes text, preserving links but removing extra HTML.
    """
    if not notes_text:
        return ""
    
    # Decode HTML entities
    notes_text = html.unescape(notes_text)
    
    # Clean up but preserve links
    # Remove &nbsp; but keep other content
    notes_text = re.sub(r'&nbsp;', ' ', notes_text)
    notes_text = re.sub(r'<br\s*/?>', ' ', notes_text, flags=re.IGNORECASE)
    
    # Normalize whitespace
    notes_text = re.sub(r'\s+', ' ', notes_text).strip()
    
    return notes_text

def parse_course_timetable_html(html_content: str) -> Dict[str, Any]:
    """
    Parse York University course timetable HTML into structured JSON.
    Handles multiple courses and multiple course variants within the same course.
    """
    # Extract metadata using regex
    title_match = re.search(r'<font color=\'#CC0000\'>(.*?)</font>', html_content)
    title = title_match.group(1) if title_match else ""
    
    updated_match = re.search(r'last updated on <strong>(.*?)</strong>', html_content)
    last_updated = updated_match.group(1) if updated_match else ""
    
    courses = []
    
    # Find all course headers using regex
    course_header_pattern = r'<td class=\'bodytext\'><strong>(\w+)</strong></td>\s*<td class=\'bodytext\'><strong>(\w+)\s*</strong></td>\s*<td class=\'bodytext\'><strong>(\w+)\s*</strong></td>\s*<td colspan=\'8\' class=\'bodytext\'><strong>(.*?)</strong></td>'
    course_headers = re.findall(course_header_pattern, html_content)
    
    # Split HTML content by course headers to process each course separately
    course_sections = re.split(course_header_pattern, html_content)
    
    # Process each course
    for i in range(len(course_headers)):
        faculty, department, term, course_title = course_headers[i]
        
        # Get the HTML section for this course
        course_content_index = (i * 5) + 5
        if course_content_index < len(course_sections):
            course_html = course_sections[course_content_index]
        else:
            continue
        
        # Find all course variants (different modes) within this course
        course_variant_pattern = r'<td class=\'smallbodytext\'>(\d+)\s+&nbsp;([\d.]+)&nbsp;(\w+)&nbsp;</td>'
        course_variants = re.findall(course_variant_pattern, course_html)
        
        if not course_variants:
            continue
        
        # For courses with multiple variants, we'll create separate entries or combine them
        # Let's combine them into one course with multiple section groups
        
        course = {
            "faculty": faculty,
            "department": department,
            "term": term.strip(),
            "courseTitle": course_title,
            "courseId": course_variants[0][0],  # Use the first course ID
            "credits": course_variants[0][1],   # Use the first credits
            "modes": list(set([variant[2] for variant in course_variants])),  # All unique modes
            "languageOfInstruction": "",
            "sections": []
        }
        
        # Extract language of instruction
        loi_pattern = r'<td class=\'smallbodytext\'>(\w+)</td>'
        loi_match = re.search(loi_pattern, course_html)
        if loi_match:
            course["languageOfInstruction"] = loi_match.group(1)
        
        # Extract all sections (LECT, TUTR, LAB, SEMR)
        section_patterns = [
            (r'<td class=\'smallbodytext\'>LECT&nbsp;</td>\s*<td class=\'smallbodytext\'>(\d+)&nbsp;</td>\s*<td class=\'smallbodytext\'>(.*?)&nbsp;</td>', 'LECT'),
            (r'<td class=\'smallbodytext\'>TUTR&nbsp;</td>\s*<td class=\'smallbodytext\'>(\d+)&nbsp;</td>\s*<td class=\'smallbodytext\'>(.*?)&nbsp;</td>', 'TUTR'),
            (r'<td class=\'smallbodytext\'>LAB\s*&nbsp;</td>\s*<td class=\'smallbodytext\'>(\d+)&nbsp;</td>\s*<td class=\'smallbodytext\'>(.*?)&nbsp;</td>', 'LAB'),
            (r'<td class=\'smallbodytext\'>SEMR&nbsp;</td>\s*<td class=\'smallbodytext\'>(\d+)&nbsp;</td>\s*<td class=\'smallbodytext\'>(.*?)&nbsp;</td>', 'SEMR'),
            (r'<td class=\'smallbodytext\'>ONLN&nbsp;</td>\s*<td class=\'smallbodytext\'>(\d+)&nbsp;</td>\s*<td class=\'smallbodytext\'>(.*?)&nbsp;</td>', 'ONLN')
        ]
        
        # Extract all schedule entries
        schedule_pattern = r'<td class=\'smallbodytext\' width=10%>([MTWRF])</td><td class=\'smallbodytext\' width=25%>([\d:]+)</td><td class=\'smallbodytext\' width=20%>(\d+)</td><td class=\'smallbodytext\' width=10%>(\w+)</td><td class=\'smallbodytext\' width=35%>(.*?)\s*</td>'
        all_schedules = re.findall(schedule_pattern, course_html)
        
        # Extract instructor information
        instructor_pattern = r'<td width=\'10%\' class=\'smallbodytext\'>(.*?)</td>'
        instructor_matches = re.findall(instructor_pattern, course_html, re.DOTALL)
        
        # Extract notes information
        notes_pattern = r'<td class=\'smallbodytext\'>(.*?)</td></tr>'
        notes_matches = re.findall(notes_pattern, course_html, re.DOTALL)
        
        schedule_index = 0
        instructor_index = 0
        notes_index = 0
        
        # Process each section type
        for pattern, section_type in section_patterns:
            section_matches = re.findall(pattern, course_html)
            
            for meet_num, cat_num in section_matches:
                # Determine how many schedule entries this section has
                if section_type in ['LECT']:
                    # Lectures typically have 1 schedule entry for this course
                    schedule_count = 1
                elif section_type in ['TUTR', 'LAB', 'SEMR']:
                    # Tutorials, labs, seminars typically have 1 schedule entry
                    schedule_count = 1
                else:
                    schedule_count = 1
                
                # Extract schedule for this section
                section_schedule = []
                for j in range(schedule_count):
                    if schedule_index + j < len(all_schedules):
                        day, time, duration, campus, room = all_schedules[schedule_index + j]
                        cleaned_room = clean_room(room)  # Clean the room field
                        section_schedule.append({
                            "day": day,
                            "time": time,
                            "duration": duration,
                            "campus": campus,
                            "room": cleaned_room
                        })
                
                schedule_index += schedule_count
                
                # Get instructors for this section
                instructors = []
                if section_type in ['LECT', 'SEMR'] and instructor_index < len(instructor_matches):
                    instructor_text = instructor_matches[instructor_index]
                    instructors = parse_instructors(instructor_text)
                    instructor_index += 1
                
                # Get notes for this section
                notes = ""
                # Look for notes that contain meaningful content (not just empty or backup)
                for note_match in notes_matches:
                    if any(keyword in note_match.lower() for keyword in ['section', 'program', 'apply', 'backup']):
                        notes = parse_notes(note_match)
                        break
                
                # Add section
                section = {
                    "type": section_type,
                    "meetNumber": meet_num,
                    "catalogNumber": cat_num.strip(),
                    "schedule": section_schedule,
                    "instructors": instructors,
                    "notes": notes
                }
                course["sections"].append(section)
        
        courses.append(course)
    
    return {
        "metadata": {
            "title": title,
            "lastUpdated": last_updated,
            "source": "York University"
        },
        "courses": courses
    }

def main():
    """
    Main function to read HTML file and output JSON.
    """
    # Read HTML file
    try:
        with open('scraping/page_source/lassonde.html', 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print("Error: lassonde.html file not found")
        print("Please save your HTML content to a file named 'lassonde.html'")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Parse HTML
    try:
        result = parse_course_timetable_html(html_content)
        
        # Output JSON
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        
        # Save to lassonde.json
        with open('scraping/data/lassonde.json', 'w', encoding='utf-8') as file:
            file.write(json_output)
        
        print("Successfully parsed HTML and saved to lassonde.json")
        print(f"Found {len(result.get('courses', []))} courses")
        
        # Print course summary
        for i, course in enumerate(result.get('courses', []), 1):
            modes_str = ', '.join(course.get('modes', []))
            print(f"{i}. {course['courseId']} - {course['courseTitle']} (Modes: {modes_str}) ({len(course['sections'])} sections)")
            
            # Print instructor info for each section
            for section in course['sections']:
                if section['instructors']:
                    instructors_str = ', '.join(section['instructors'])
                    print(f"   {section['type']} {section['meetNumber']}: {instructors_str}")
        
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()