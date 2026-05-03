"""
Test cases for generate_seed.py
"""

import unittest
import json
import tempfile
import os
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import patch, mock_open
from generate_seed import (
    escape_sql_string,
    format_schedule,
    parse_instructor_name,
    generate_rate_my_prof_url,
    load_course_descriptions,
    collect_courses_and_instructors,
    process_sections,
    generate_instructor_sql,
    generate_course_sql,
    generate_section_activity_sql,
    generate_section_sql,
    generate_seed_sql
)


class TestEscapeSQLString(unittest.TestCase):
    """Test escape_sql_string function"""
    
    def test_normal_string(self):
        self.assertEqual(escape_sql_string("John Doe"), "'John Doe'")
    
    def test_string_with_single_quote(self):
        self.assertEqual(escape_sql_string("O'Brien"), "'O''Brien'")
    
    def test_string_with_multiple_quotes(self):
        self.assertEqual(escape_sql_string("It's John's book"), "'It''s John''s book'")
    
    def test_none_value(self):
        self.assertEqual(escape_sql_string(None), 'NULL')
    
    def test_empty_string(self):
        self.assertEqual(escape_sql_string(""), "''")


class TestFormatSchedule(unittest.TestCase):
    """Test format_schedule function"""
    
    def test_empty_schedule(self):
        self.assertEqual(format_schedule([]), 'NULL')
    
    def test_single_item_schedule(self):
        schedule = [{"day": "M", "time": "10:00", "duration": "50"}]
        result = format_schedule(schedule)
        self.assertTrue(result.startswith("'"))
        self.assertTrue(result.endswith("'"))
        self.assertIn("M", result)
        self.assertIn("10:00", result)
    
    def test_multiple_items_schedule(self):
        schedule = [
            {"day": "M", "time": "10:00", "duration": "50"},
            {"day": "W", "time": "10:00", "duration": "50"}
        ]
        result = format_schedule(schedule)
        self.assertTrue(result.startswith("'"))
        self.assertTrue("M" in result and "W" in result)


class TestParseInstructorName(unittest.TestCase):
    """Test parse_instructor_name function"""
    
    def test_single_name(self):
        self.assertEqual(parse_instructor_name("John"), ("John", ""))
    
    def test_two_names(self):
        self.assertEqual(parse_instructor_name("John Doe"), ("John", "Doe"))
    
    def test_three_names(self):
        self.assertEqual(parse_instructor_name("John Michael Doe"), ("John Michael", "Doe"))
    
    def test_four_names(self):
        self.assertEqual(parse_instructor_name("Mary Jane Watson Parker"), ("Mary Jane Watson", "Parker"))
    
    def test_empty_string(self):
        self.assertEqual(parse_instructor_name(""), ("", ""))
    
    def test_whitespace_only(self):
        self.assertEqual(parse_instructor_name("   "), ("", ""))
    
    def test_leading_trailing_whitespace(self):
        self.assertEqual(parse_instructor_name("  John Doe  "), ("John", "Doe"))


class TestGenerateRateMyProfURL(unittest.TestCase):
    """Test generate_rate_my_prof_url function"""
    
    def test_both_names_provided(self):
        url = generate_rate_my_prof_url("John", "Doe")
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith("https://www.ratemyprofessors.com"))
        self.assertIn("John", url)
        self.assertIn("Doe", url)
    
    def test_only_first_name(self):
        url = generate_rate_my_prof_url("John", "")
        self.assertIsNotNone(url)
        self.assertIn("John", url)
    
    def test_only_last_name(self):
        url = generate_rate_my_prof_url("", "Doe")
        self.assertIsNotNone(url)
        self.assertIn("Doe", url)
    
    def test_both_empty(self):
        self.assertIsNone(generate_rate_my_prof_url("", ""))
    
    def test_url_encoding(self):
        url = generate_rate_my_prof_url("Mary Jane", "Watson")
        self.assertIn("Mary+Jane", url)
        self.assertIn("Watson", url)
    
    def test_whitespace_only_names(self):
        self.assertIsNone(generate_rate_my_prof_url("   ", "   "))
    
    def test_first_name_whitespace_last_name_whitespace(self):
        self.assertIsNone(generate_rate_my_prof_url(" ", " "))


class TestLoadCourseDescriptions(unittest.TestCase):
    """Test load_course_descriptions function"""
    
    def test_load_valid_descriptions(self):
        descriptions_data = [
            {"course_code": "EECS1000", "description": "Introduction to CS"},
            {"course_code": "MATH1090", "description": "Introduction to Math"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(descriptions_data, f)
            temp_file = f.name
        
        try:
            descriptions_map = load_course_descriptions(temp_file)
            
            self.assertEqual(len(descriptions_map), 2)
            self.assertEqual(descriptions_map["EECS1000"], "Introduction to CS")
            self.assertEqual(descriptions_map["MATH1090"], "Introduction to Math")
        finally:
            os.unlink(temp_file)
    
    def test_load_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_file = f.name
        
        try:
            descriptions_map = load_course_descriptions(temp_file)
            self.assertEqual(len(descriptions_map), 0)
        finally:
            os.unlink(temp_file)
    
    def test_load_nonexistent_file(self):
        descriptions_map = load_course_descriptions("/nonexistent/path/file.json")
        self.assertEqual(len(descriptions_map), 0)
    
    def test_skip_entries_without_code(self):
        descriptions_data = [
            {"course_code": "EECS1000", "description": "Introduction to CS"},
            {"description": "No code"},
            {"course_code": "", "description": "Empty code"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(descriptions_data, f)
            temp_file = f.name
        
        try:
            descriptions_map = load_course_descriptions(temp_file)
            self.assertEqual(len(descriptions_map), 1)
            self.assertIn("EECS1000", descriptions_map)
        finally:
            os.unlink(temp_file)
    
    def test_skip_entries_without_description(self):
        descriptions_data = [
            {"course_code": "EECS1000", "description": "Introduction to CS"},
            {"course_code": "MATH1090"},
            {"course_code": "PHYS1010", "description": ""}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(descriptions_data, f)
            temp_file = f.name
        
        try:
            descriptions_map = load_course_descriptions(temp_file)
            self.assertEqual(len(descriptions_map), 1)
            self.assertIn("EECS1000", descriptions_map)
        finally:
            os.unlink(temp_file)

    def test_invalid_json_logs_warning(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{invalid json')
            temp_file = f.name

        try:
            with patch('builtins.print') as mock_print:
                descriptions_map = load_course_descriptions(temp_file)
                self.assertEqual(len(descriptions_map), 0)
                self.assertTrue(any('Warning: Error loading course descriptions' in str(call) for call in mock_print.call_args_list))
        finally:
            os.unlink(temp_file)


class TestCollectCoursesAndInstructors(unittest.TestCase):
    """Test collect_courses_and_instructors function"""
    
    def test_single_course(self):
        courses = [{
            'courseTitle': 'Introduction to CS',
            'department': 'EECS',
            'courseId': '1000',
            'credits': '3.00',
            'notes': 'Basic course',
            'faculty': 'LE',
            'term': 'F',
            'sections': []
        }]
        
        courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors(courses)
        
        self.assertEqual(len(courses_list), 1)
        self.assertEqual(courses_list[0]['code'], 'EECS1000')
        self.assertEqual(courses_list[0]['name'], 'Introduction to CS')
        self.assertEqual(courses_list[0]['credits'], 3.0)
        self.assertEqual(courses_list[0]['faculty'], 'LE')
        self.assertEqual(courses_list[0]['term'], 'F')
        self.assertIn('EECS1000_F', course_code_to_uuid)
        self.assertIn('EECS1000_F', course_code_to_index)
    
    def test_duplicate_courses_same_term_deduplication(self):
        courses = [
            {
                'courseTitle': 'Introduction to CS',
                'department': 'EECS',
                'courseId': '1000',
                'credits': '3.00',
                'notes': '',
                'faculty': 'LE',
                'term': 'F',
                'sections': []
            },
            {
                'courseTitle': 'Introduction to CS',
                'department': 'EECS',
                'courseId': '1000',
                'credits': '3.00',
                'notes': '',
                'faculty': 'LE',
                'term': 'F',
                'sections': []
            }
        ]
        
        courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors(courses)
        
        self.assertEqual(len(courses_list), 1)  # Should be deduplicated (same code + term)
        self.assertEqual(len(course_code_to_uuid), 1)
    
    def test_duplicate_courses_different_terms(self):
        courses = [
            {
                'courseTitle': 'Introduction to CS',
                'department': 'EECS',
                'courseId': '1000',
                'credits': '3.00',
                'notes': '',
                'faculty': 'LE',
                'term': 'F',
                'sections': []
            },
            {
                'courseTitle': 'Introduction to CS',
                'department': 'EECS',
                'courseId': '1000',
                'credits': '3.00',
                'notes': '',
                'faculty': 'LE',
                'term': 'W',
                'sections': []
            }
        ]
        
        courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors(courses)
        
        self.assertEqual(len(courses_list), 2)  # Should create separate courses (different terms)
        self.assertEqual(len(course_code_to_uuid), 2)
        self.assertIn('EECS1000_F', course_code_to_uuid)
        self.assertIn('EECS1000_W', course_code_to_uuid)
    
    def test_course_without_faculty_term(self):
        courses = [{
            'courseTitle': 'Introduction to CS',
            'department': 'EECS',
            'courseId': '1000',
            'credits': '3.00',
            'notes': 'Basic course',
            'sections': []
        }]
        
        courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors(courses)
        
        self.assertEqual(len(courses_list), 1)
        self.assertEqual(courses_list[0]['faculty'], '')
        self.assertEqual(courses_list[0]['term'], '')
        self.assertIn('EECS1000_', course_code_to_uuid)
    
    def test_empty_courses_list(self):
        courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors([])
        
        self.assertEqual(len(courses_list), 0)
        self.assertEqual(len(course_code_to_uuid), 0)
        self.assertEqual(len(course_code_to_index), 0)
    
    def test_invalid_credits(self):
        courses = [{
            'courseTitle': 'Test Course',
            'department': 'TEST',
            'courseId': '1000',
            'credits': 'invalid',
            'notes': '',
            'faculty': 'LE',
            'term': 'F',
            'sections': []
        }]
        
        courses_list, _, _ = collect_courses_and_instructors(courses)
        
        self.assertEqual(len(courses_list), 1)
        self.assertEqual(courses_list[0]['credits'], 0.0)  # Should default to 0.0 on error
    
    def test_none_credits(self):
        courses = [{
            'courseTitle': 'Test Course',
            'department': 'TEST',
            'courseId': '1000',
            'credits': None,
            'notes': '',
            'faculty': 'LE',
            'term': 'F',
            'sections': []
        }]
        
        courses_list, _, _ = collect_courses_and_instructors(courses)
        
        self.assertEqual(len(courses_list), 1)
        self.assertEqual(courses_list[0]['credits'], 0.0)
    
    def test_with_descriptions_map(self):
        descriptions_map = {
            'TEST1000': 'Description from map'
        }
        
        courses = [{
            'courseTitle': 'Test Course',
            'department': 'TEST',
            'courseId': '1000',
            'credits': '3.00',
            'notes': 'Description from notes',
            'faculty': 'LE',
            'term': 'F',
            'sections': []
        }]
        
        courses_list, _, _ = collect_courses_and_instructors(courses, descriptions_map)
        
        self.assertEqual(len(courses_list), 1)
        self.assertEqual(courses_list[0]['description'], 'Description from map')
    
    def test_descriptions_map_fallback_to_notes(self):
        descriptions_map = {
            'OTHER1000': 'Other description'
        }
        
        courses = [{
            'courseTitle': 'Test Course',
            'department': 'TEST',
            'courseId': '1000',
            'credits': '3.00',
            'notes': 'Description from notes',
            'faculty': 'LE',
            'term': 'F',
            'sections': []
        }]
        
        courses_list, _, _ = collect_courses_and_instructors(courses, descriptions_map)
        
        self.assertEqual(len(courses_list), 1)
        self.assertEqual(courses_list[0]['description'], 'Description from notes')
    
    def test_no_descriptions_map(self):
        courses = [{
            'courseTitle': 'Test Course',
            'department': 'TEST',
            'courseId': '1000',
            'credits': '3.00',
            'notes': 'Description from notes',
            'faculty': 'LE',
            'term': 'F',
            'sections': []
        }]
        
        courses_list, _, _ = collect_courses_and_instructors(courses, None)
        
        self.assertEqual(len(courses_list), 1)
        self.assertEqual(courses_list[0]['description'], 'Description from notes')


class TestProcessSections(unittest.TestCase):
    """Test process_sections function"""
    
    def setUp(self):
        # Create a course with index mapping (using course_key format: code_term)
        self.course_code_to_index = {'EECS1000_F': 0}
        self.courses_list = [{'uuid': str(uuid.uuid4())}]
    
    def test_lecture_section(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [{
                'type': 'LECT',
                'catalogNumber': '',
                'schedule': [{'day': 'M', 'time': '10:00', 'duration': '50'}],
                'meetNumber': '01',
                'section': 'A',
                'instructors': ['John Doe']
            }]
        }]
        
        activities, sections, instructors = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]['letter'], 'A')
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0]['course_type'], 'LECT')
        self.assertNotEqual(activities[0]['times'], 'NULL')
        self.assertEqual(len(instructors), 1)
        self.assertEqual(instructors[0]['name'], 'John Doe')
        self.assertIn('section_uuid', instructors[0])
    
    def test_lab_section_with_lecture(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [
                {
                    'type': 'LECT',
                    'catalogNumber': '',
                    'schedule': [],
                    'meetNumber': '01',
                    'section': 'A',
                    'instructors': []
                },
                {
                    'type': 'LAB',
                    'catalogNumber': 'L01',
                    'schedule': [{'day': 'T', 'time': '14:00'}],
                    'meetNumber': '01',
                    'instructors': []
                }
            ]
        }]
        
        activities, sections, instructors = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(activities), 2)  # LECT + LAB
        lab_activities = [a for a in activities if a['course_type'] == 'LAB']
        self.assertEqual(len(lab_activities), 1)
        self.assertEqual(lab_activities[0]['catalog_number'], 'L01')
        self.assertIn('section_uuid', lab_activities[0])
        self.assertEqual(lab_activities[0]['section_uuid'], sections[0]['uuid'])
    
    def test_tutorial_section_with_lecture(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [
                {
                    'type': 'LECT',
                    'catalogNumber': '',
                    'schedule': [],
                    'meetNumber': '01',
                    'section': 'A',
                    'instructors': []
                },
                {
                    'type': 'TUT',
                    'catalogNumber': 'T01',
                    'schedule': [{'day': 'W', 'time': '12:00'}],
                    'meetNumber': '01',
                    'instructors': []
                }
            ]
        }]
        
        activities, sections, instructors = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(activities), 2)  # LECT + TUT
        tut_activities = [a for a in activities if a['course_type'] == 'TUT']
        self.assertEqual(len(tut_activities), 1)
        self.assertEqual(tut_activities[0]['catalog_number'], 'T01')
        self.assertIn('section_uuid', tut_activities[0])
        self.assertEqual(tut_activities[0]['section_uuid'], sections[0]['uuid'])
    
    def test_multiple_instructors(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [{
                'type': 'LECT',
                'catalogNumber': '',
                'schedule': [],
                'meetNumber': '01',
                'section': 'A',
                'instructors': ['John Doe', 'Jane Smith']
            }]
        }]
        
        _, _, instructors = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(instructors), 2)
        names = [inst['name'] for inst in instructors]
        self.assertIn('John Doe', names)
        self.assertIn('Jane Smith', names)
    
    def test_unknown_course_code(self):
        courses = [{
            'department': 'MATH',
            'courseId': '9999',
            'term': 'F',
            'sections': [{
                'type': 'LECT',
                'catalogNumber': '',
                'schedule': [],
                'meetNumber': '01',
                'instructors': []
            }]
        }]
        
        activities, sections, instructors = process_sections(courses, self.course_code_to_index)
        
        # Should skip unknown course
        self.assertEqual(len(activities), 0)
        self.assertEqual(len(sections), 0)
        self.assertEqual(len(instructors), 0)
    
    def test_lecture_with_schedule(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [{
                'type': 'LECT',
                'catalogNumber': '',
                'schedule': [
                    {'day': 'M', 'time': '10:00', 'duration': '50', 'campus': 'Keele', 'room': 'MC 101'},
                    {'day': 'W', 'time': '10:00', 'duration': '50', 'campus': 'Keele', 'room': 'MC 101'}
                ],
                'meetNumber': '01',
                'section': 'A',
                'instructors': []
            }]
        }]
        
        activities, sections, _ = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0]['course_type'], 'LECT')
        times_json = activities[0]['times']
        self.assertTrue(times_json.startswith("'") and times_json.endswith("'"))
        self.assertIn('M', times_json)
        self.assertIn('W', times_json)
    
    def test_lab_without_lecture_finds_first(self):
        """Test that lab without preceding lecture finds first LECT section"""
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [
                {
                    'type': 'LECT',
                    'catalogNumber': '',
                    'schedule': [],
                    'meetNumber': '01',
                    'section': 'A',
                    'instructors': []
                },
                {
                    'type': 'LAB',
                    'catalogNumber': 'L01',
                    'schedule': [{'day': 'T', 'time': '14:00'}],
                    'meetNumber': '01',
                    'instructors': []
                }
            ]
        }]
        
        activities, sections, _ = process_sections(courses, self.course_code_to_index)
        
        # Lab should be associated with the LECT section
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(activities), 2)  # LECT + LAB
        lab_activities = [a for a in activities if a['course_type'] == 'LAB']
        self.assertEqual(len(lab_activities), 1)
        self.assertEqual(lab_activities[0]['section_uuid'], sections[0]['uuid'])
    
    def test_tutorial_without_lecture_finds_first(self):
        """Test that tutorial without preceding lecture finds first LECT section"""
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [
                {
                    'type': 'LECT',
                    'catalogNumber': '',
                    'schedule': [],
                    'meetNumber': '01',
                    'section': 'A',
                    'instructors': []
                },
                {
                    'type': 'TUT',
                    'catalogNumber': 'T01',
                    'schedule': [{'day': 'W', 'time': '12:00'}],
                    'meetNumber': '01',
                    'instructors': []
                }
            ]
        }]
        
        activities, sections, _ = process_sections(courses, self.course_code_to_index)
        
        # Tutorial should be associated with the LECT section
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(activities), 2)  # LECT + TUT
        tut_activities = [a for a in activities if a['course_type'] == 'TUT']
        self.assertEqual(len(tut_activities), 1)
        self.assertEqual(tut_activities[0]['section_uuid'], sections[0]['uuid'])
    
    def test_online_section(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [{
                'type': 'ONLN',
                'catalogNumber': '',
                'schedule': [],
                'meetNumber': '01',
                'section': 'A',
                'instructors': ['John Doe']
            }]
        }]
        
        _, sections, instructors = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(instructors), 1)
    
    def test_lab_before_lecture_no_association(self):
        """Test edge case: LAB appears before LECT, cannot associate (no section yet)"""
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [
                {
                    'type': 'LAB',
                    'catalogNumber': 'L01',
                    'schedule': [{'day': 'T', 'time': '14:00'}],
                    'meetNumber': '01',
                    'instructors': []
                },
                {
                    'type': 'LECT',
                    'catalogNumber': '',
                    'schedule': [],
                    'meetNumber': '01',
                    'section': 'A',
                    'instructors': []
                }
            ]
        }]
        
        activities, sections, _ = process_sections(courses, self.course_code_to_index)
        
        # With new logic, sections are created in first pass, so LAB can be associated
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(activities), 2)  # LAB + LECT
        lab_activities = [a for a in activities if a['course_type'] == 'LAB']
        self.assertEqual(len(lab_activities), 1)
        self.assertEqual(lab_activities[0]['section_uuid'], sections[0]['uuid'])
    
    def test_tutorial_before_lecture_no_association(self):
        """Test edge case: TUT appears before LECT, cannot associate (no section yet)"""
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [
                {
                    'type': 'TUT',
                    'catalogNumber': 'T01',
                    'schedule': [{'day': 'W', 'time': '12:00'}],
                    'meetNumber': '01',
                    'instructors': []
                },
                {
                    'type': 'LECT',
                    'catalogNumber': '',
                    'schedule': [],
                    'meetNumber': '01',
                    'section': 'A',
                    'instructors': []
                }
            ]
        }]
        
        activities, sections, _ = process_sections(courses, self.course_code_to_index)
        
        # With new logic, sections are created in first pass, so TUT can be associated
        self.assertEqual(len(sections), 1)
        self.assertEqual(len(activities), 2)  # TUT + LECT
        tut_activities = [a for a in activities if a['course_type'] == 'TUT']
        self.assertEqual(len(tut_activities), 1)
        self.assertEqual(tut_activities[0]['section_uuid'], sections[0]['uuid'])
    
    def test_lab_after_multiple_lectures_finds_first(self):
        """Test that lab after multiple lectures finds first LECT when current_section_uuid is None"""
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'term': 'F',
            'sections': [
                {
                    'type': 'LECT',
                    'catalogNumber': '',
                    'schedule': [],
                    'meetNumber': '01',
                    'section': 'A',
                    'instructors': []
                },
                {
                    'type': 'LECT',
                    'catalogNumber': '',
                    'schedule': [],
                    'meetNumber': '02',
                    'section': 'B',
                    'instructors': []
                },
                {
                    'type': 'LAB',
                    'catalogNumber': 'L01',
                    'schedule': [{'day': 'T', 'time': '14:00'}],
                    'meetNumber': '01',
                    'instructors': []
                }
            ]
        }]
        
        activities, sections, _ = process_sections(courses, self.course_code_to_index)
        
        # Lab should be associated with one of the sections
        self.assertEqual(len(sections), 2)
        self.assertEqual(len(activities), 3)  # LECT A + LECT B + LAB
        lab_activities = [a for a in activities if a['course_type'] == 'LAB']
        self.assertEqual(len(lab_activities), 1)
        # The lab should be associated with one of the sections
        self.assertIn(lab_activities[0]['section_uuid'], [s['uuid'] for s in sections])


class TestGenerateInstructorSQL(unittest.TestCase):
    """Test generate_instructor_sql function"""
    
    def test_single_instructor(self):
        section_uuid = str(uuid.uuid4())
        instructors_list = [{
            'name': 'John Doe',
            'section_uuid': section_uuid
        }]
        sql_lines = generate_instructor_sql(instructors_list)
        
        self.assertGreater(len(sql_lines), 0)
        self.assertIn('-- Insert instructors', sql_lines)
        sql_content = '\n'.join(sql_lines)
        self.assertIn('INSERT INTO instructors', sql_content)
        self.assertIn('John', sql_content)
        self.assertIn('Doe', sql_content)
        self.assertIn(section_uuid, sql_content)
    
    def test_multiple_instructors(self):
        section_uuid = str(uuid.uuid4())
        instructors_list = [
            {'name': 'John Doe', 'section_uuid': section_uuid},
            {'name': 'Jane Smith', 'section_uuid': section_uuid}
        ]
        sql_lines = generate_instructor_sql(instructors_list)
        
        sql_content = '\n'.join(sql_lines)
        self.assertIn('John', sql_content)
        self.assertIn('Jane', sql_content)
    
    def test_empty_instructors(self):
        sql_lines = generate_instructor_sql([])
        
        self.assertEqual(len(sql_lines), 1)  # Just the comment
        self.assertIn('-- Insert instructors', sql_lines)


class TestGenerateCourseSQL(unittest.TestCase):
    """Test generate_course_sql function"""
    
    def test_single_course(self):
        courses_list = [{
            'uuid': str(uuid.uuid4()),
            'code': 'EECS1000',
            'name': 'Introduction to CS',
            'credits': 3.0,
            'description': 'Basic course',
            'faculty': 'LE',
            'term': 'F'
        }]
        
        sql_lines = generate_course_sql(courses_list)
        sql_content = '\n'.join(sql_lines)
        
        self.assertIn('-- Insert courses', sql_lines)
        self.assertIn('INSERT INTO courses', sql_content)
        self.assertIn('EECS1000', sql_content)
        self.assertIn('Introduction to CS', sql_content)
        self.assertIn('LE', sql_content)
        self.assertIn('F', sql_content)
    
    def test_course_with_null_description(self):
        courses_list = [{
            'uuid': str(uuid.uuid4()),
            'code': 'EECS1000',
            'name': 'Introduction to CS',
            'credits': 3.0,
            'description': '',
            'faculty': 'LE',
            'term': 'F'
        }]
        
        sql_lines = generate_course_sql(courses_list)
        sql_content = '\n'.join(sql_lines)
        
        self.assertIn('NULL', sql_content)
    
    def test_course_without_faculty_term(self):
        courses_list = [{
            'uuid': str(uuid.uuid4()),
            'code': 'EECS1000',
            'name': 'Introduction to CS',
            'credits': 3.0,
            'description': 'Basic course'
        }]
        
        sql_lines = generate_course_sql(courses_list)
        sql_content = '\n'.join(sql_lines)
        
        # Should still generate SQL with NULL for faculty and term
        self.assertIn('INSERT INTO courses', sql_content)
        # Count NULL occurrences - should be at least 2 (description, faculty, term could be NULL)
        null_count = sql_content.count('NULL')
        self.assertGreaterEqual(null_count, 2)


class TestGenerateSectionActivitySQL(unittest.TestCase):
    """Test generate_section_activity_sql function"""
    
    def test_single_activity(self):
        section_uuid = str(uuid.uuid4())
        activities_list = [{
            'section_uuid': section_uuid,
            'course_type': 'LAB',
            'catalog_number': 'L01',
            'times': "'[{\"day\": \"M\"}]'"
        }]
        
        sql_lines = generate_section_activity_sql(activities_list)
        sql_content = '\n'.join(sql_lines)
        
        self.assertIn('-- Insert section activities', sql_lines)
        self.assertIn('INSERT INTO section_activities', sql_content)
        self.assertIn('LAB', sql_content)
        self.assertIn('L01', sql_content)
        self.assertIn(section_uuid, sql_content)
    
    def test_multiple_activities(self):
        section_uuid = str(uuid.uuid4())
        activities_list = [
            {
                'section_uuid': section_uuid,
                'course_type': 'LECT',
                'catalog_number': '',
                'times': "'[{\"day\": \"M\"}]'"
            },
            {
                'section_uuid': section_uuid,
                'course_type': 'LAB',
                'catalog_number': 'L01',
                'times': "'[{\"day\": \"T\"}]'"
            }
        ]
        
        sql_lines = generate_section_activity_sql(activities_list)
        sql_content = '\n'.join(sql_lines)
        
        self.assertIn('LECT', sql_content)
        self.assertIn('LAB', sql_content)
        self.assertIn('L01', sql_content)
    
    def test_empty_activities(self):
        sql_lines = generate_section_activity_sql([])
        
        self.assertEqual(len(sql_lines), 1)  # Just the comment
        self.assertIn('-- Insert section activities', sql_lines)


class TestGenerateSectionSQL(unittest.TestCase):
    """Test generate_section_sql function"""
    
    def test_single_section(self):
        course_uuid = str(uuid.uuid4())
        courses_list = [{'uuid': course_uuid}]
        sections_list = [{
            'uuid': str(uuid.uuid4()),
            'course_idx': 0,
            'letter': 'A'
        }]
        
        sql_lines = generate_section_sql(sections_list, courses_list)
        sql_content = '\n'.join(sql_lines)
        
        self.assertIn('-- Insert sections', sql_lines)
        self.assertIn('INSERT INTO sections', sql_content)
        self.assertIn("'A'", sql_content)
        self.assertIn(course_uuid, sql_content)
        self.assertNotIn('times', sql_content.lower())
    
    def test_section_basic(self):
        course_uuid = str(uuid.uuid4())
        courses_list = [{'uuid': course_uuid}]
        sections_list = [{
            'uuid': str(uuid.uuid4()),
            'course_idx': 0,
            'letter': 'M'
        }]
        
        sql_lines = generate_section_sql(sections_list, courses_list)
        sql_content = '\n'.join(sql_lines)
        
        self.assertIn('INSERT INTO sections', sql_content)
        self.assertIn("'M'", sql_content)
        self.assertIn(course_uuid, sql_content)
    
    def test_empty_sections(self):
        courses_list = []
        sql_lines = generate_section_sql([], courses_list)
        
        self.assertEqual(len(sql_lines), 1)  # Just the comment
        self.assertIn('-- Insert sections', sql_lines)


class TestGenerateSeedSQLIntegration(unittest.TestCase):
    """Integration test for generate_seed_sql function"""
    
    def setUp(self):
        self.test_json_1 = {
            'courses': [
                {
                    'courseTitle': 'Test Course 1',
                    'department': 'TEST',
                    'courseId': '1000',
                    'credits': '3.00',
                    'notes': 'Test description 1',
                    'faculty': 'LE',
                    'term': 'F',
                    'sections': [
                        {
                            'type': 'LECT',
                            'catalogNumber': '',
                            'schedule': [{'day': 'M', 'time': '10:00', 'duration': '50'}],
                            'meetNumber': '01',
                            'section': 'A',
                            'instructors': ['John Doe']
                        }
                    ]
                }
            ]
        }
        self.test_json_2 = {
            'courses': [
                {
                    'courseTitle': 'Test Course 2',
                    'department': 'TEST',
                    'courseId': '2000',
                    'credits': '4.00',
                    'notes': 'Test description 2',
                    'faculty': 'LE',
                    'term': 'W',
                    'sections': [
                        {
                            'type': 'LECT',
                            'catalogNumber': '',
                            'schedule': [],
                            'meetNumber': '01',
                            'section': 'B',
                            'instructors': []
                        },
                        {
                            'type': 'LAB',
                            'catalogNumber': 'L01',
                            'schedule': [{'day': 'T', 'time': '14:00', 'duration': '170'}],
                            'meetNumber': '02',
                            'instructors': ['Jane Smith']
                        }
                    ]
                }
            ]
        }
    
    def test_full_generation(self):
        json_files = []
        try:
            # Create multiple temporary JSON files
            for test_json in [self.test_json_1, self.test_json_2]:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as json_file:
                    json.dump(test_json, json_file)
                    json_files.append(json_file.name)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as sql_file:
                sql_path = sql_file.name
            
            try:
                # Pass the list of JSON files to the function
                generate_seed_sql(json_files, sql_path, None)
                
                # Verify file was created
                self.assertTrue(os.path.exists(sql_path))
                
                # Read and verify content
                with open(sql_path, 'r') as f:
                    content = f.read()
                
                self.assertIn('BEGIN;', content)
                self.assertIn('COMMIT;', content)
                self.assertIn('INSERT INTO instructors', content)
                self.assertIn('INSERT INTO courses', content)
                self.assertIn('INSERT INTO sections', content)
                self.assertIn('INSERT INTO section_activities', content)
                self.assertIn('Test Course 1', content)
                self.assertIn('Test Course 2', content)
                self.assertIn('John', content)
                self.assertIn('Doe', content)
                # Check for faculty and term
                self.assertIn('LE', content)
                self.assertIn('F', content)
                self.assertIn('W', content)
                
            finally:
                if os.path.exists(sql_path):
                    os.unlink(sql_path)
        finally:
            for json_file in json_files:
                if os.path.exists(json_file):
                    os.unlink(json_file)

    def test_generation_with_descriptions_file(self):
        descriptions = [
            {"course_code": "TEST1000", "description": "From map"}
        ]
        json_files = []
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as desc_file:
                json.dump(descriptions, desc_file)
                descriptions_path = desc_file.name

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as json_file:
                json.dump(self.test_json_1, json_file)
                json_files.append(json_file.name)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as sql_file:
                sql_path = sql_file.name

            generate_seed_sql(json_files, sql_path, descriptions_path)

            with open(sql_path, 'r') as f:
                content = f.read()

            self.assertIn('From map', content)
        finally:
            if os.path.exists(descriptions_path):
                os.unlink(descriptions_path)
            if os.path.exists(sql_path):
                os.unlink(sql_path)
            for json_file in json_files:
                if os.path.exists(json_file):
                    os.unlink(json_file)


class TestGenerateSeedMain(unittest.TestCase):
    """Test __main__ block behavior"""

    def test_main_exits_when_no_json_files(self):
        repo = Path(__file__).resolve().parents[1]
        script = repo / "scripts" / "generate_seed.py"
        with tempfile.TemporaryDirectory() as empty_a, tempfile.TemporaryDirectory() as empty_b:
            r = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    empty_a,
                    empty_b,
                    "-o",
                    str(Path(empty_a) / "out.sql"),
                ],
                cwd=str(repo),
                capture_output=True,
                text=True,
            )
        self.assertEqual(r.returncode, 1)

    def test_main_rejects_single_term_without_flag(self):
        repo = Path(__file__).resolve().parents[1]
        script = repo / "scripts" / "generate_seed.py"
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run(
                [sys.executable, str(script), td],
                cwd=str(repo),
                capture_output=True,
                text=True,
            )
        self.assertEqual(r.returncode, 2)


if __name__ == '__main__':
    unittest.main()

