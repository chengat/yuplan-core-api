"""
Test cases for generate_seed.py
"""

import unittest
import json
import tempfile
import os
import uuid
from unittest.mock import patch, mock_open
from generate_seed import (
    escape_sql_string,
    format_schedule,
    parse_instructor_name,
    generate_rate_my_prof_url,
    collect_courses_and_instructors,
    process_single_section,
    process_sections,
    generate_instructor_sql,
    generate_course_sql,
    generate_lab_sql,
    generate_tutorial_sql,
    generate_section_sql,
    generate_junction_table_sql,
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


class TestCollectCoursesAndInstructors(unittest.TestCase):
    """Test collect_courses_and_instructors function"""
    
    def test_single_course(self):
        courses = [{
            'courseTitle': 'Introduction to CS',
            'department': 'EECS',
            'courseId': '1000',
            'credits': '3.00',
            'notes': 'Basic course',
            'sections': [
                {
                    'instructors': ['John Doe']
                }
            ]
        }]
        
        instructors_map, courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors(courses)
        
        self.assertEqual(len(courses_list), 1)
        self.assertEqual(courses_list[0]['code'], 'EECS1000')
        self.assertEqual(courses_list[0]['name'], 'Introduction to CS')
        self.assertEqual(courses_list[0]['credits'], 3.0)
        self.assertIn('John Doe', instructors_map)
        self.assertEqual(instructors_map['John Doe'], ('John', 'Doe'))
    
    def test_duplicate_courses_deduplication(self):
        courses = [
            {
                'courseTitle': 'Introduction to CS',
                'department': 'EECS',
                'courseId': '1000',
                'credits': '3.00',
                'notes': '',
                'sections': []
            },
            {
                'courseTitle': 'Introduction to CS',
                'department': 'EECS',
                'courseId': '1000',
                'credits': '3.00',
                'notes': '',
                'sections': []
            }
        ]
        
        instructors_map, courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors(courses)
        
        self.assertEqual(len(courses_list), 1)  # Should be deduplicated
        self.assertEqual(len(course_code_to_uuid), 1)
    
    def test_multiple_instructors(self):
        courses = [{
            'courseTitle': 'Advanced CS',
            'department': 'EECS',
            'courseId': '2000',
            'credits': '3.00',
            'notes': '',
            'sections': [
                {'instructors': ['John Doe']},
                {'instructors': ['Jane Smith', 'Bob Wilson']}
            ]
        }]
        
        instructors_map, courses_list, _, _ = collect_courses_and_instructors(courses)
        
        self.assertIn('John Doe', instructors_map)
        self.assertIn('Jane Smith', instructors_map)
        self.assertIn('Bob Wilson', instructors_map)
    
    def test_empty_courses_list(self):
        instructors_map, courses_list, course_code_to_uuid, course_code_to_index = collect_courses_and_instructors([])
        
        self.assertEqual(len(courses_list), 0)
        self.assertEqual(len(instructors_map), 0)


class TestProcessSingleSection(unittest.TestCase):
    """Test process_single_section function"""
    
    def test_lab_section(self):
        section = {
            'type': 'LAB',
            'catalogNumber': 'L01',
            'schedule': [{'day': 'M', 'time': '10:00'}],
            'meetNumber': '01',
            'instructors': ['John Doe']
        }
        
        lab_entry, tutorial_entry, section_entry, instructor_links = process_single_section(
            section, 0, 'EECS1000'
        )
        
        self.assertIsNotNone(lab_entry)
        self.assertEqual(lab_entry['catalog_number'], 'L01')
        self.assertIsNone(tutorial_entry)
        self.assertIsNone(section_entry)
        self.assertEqual(len(instructor_links), 1)
        self.assertEqual(instructor_links[0], ('John Doe', 'EECS1000'))
    
    def test_tutorial_section(self):
        section = {
            'type': 'TUT',
            'catalogNumber': 'T01',
            'schedule': [],
            'meetNumber': '01',
            'instructors': []
        }
        
        lab_entry, tutorial_entry, section_entry, instructor_links = process_single_section(
            section, 0, 'EECS1000'
        )
        
        self.assertIsNone(lab_entry)
        self.assertIsNotNone(tutorial_entry)
        self.assertEqual(tutorial_entry['catalog_number'], 'T01')
        self.assertIsNone(section_entry)
        self.assertEqual(len(instructor_links), 0)
    
    def test_lecture_section(self):
        section = {
            'type': 'LECT',
            'catalogNumber': '',
            'schedule': [],
            'meetNumber': '02',
            'instructors': ['Jane Smith']
        }
        
        lab_entry, tutorial_entry, section_entry, instructor_links = process_single_section(
            section, 0, 'EECS1000'
        )
        
        self.assertIsNone(lab_entry)
        self.assertIsNone(tutorial_entry)
        self.assertIsNotNone(section_entry)
        self.assertEqual(section_entry['letter'], '02')
        self.assertEqual(len(instructor_links), 1)
    
    def test_online_section(self):
        section = {
            'type': 'ONLN',
            'catalogNumber': '',
            'schedule': [],
            'meetNumber': '01',
            'instructors': []
        }
        
        lab_entry, tutorial_entry, section_entry, instructor_links = process_single_section(
            section, 0, 'EECS1000'
        )
        
        self.assertIsNone(lab_entry)
        self.assertIsNone(tutorial_entry)
        self.assertIsNotNone(section_entry)
    
    def test_unknown_section_type(self):
        section = {
            'type': 'UNKNOWN',
            'catalogNumber': '',
            'schedule': [],
            'meetNumber': '01',
            'instructors': []
        }
        
        lab_entry, tutorial_entry, section_entry, instructor_links = process_single_section(
            section, 0, 'EECS1000'
        )
        
        self.assertIsNone(lab_entry)
        self.assertIsNone(tutorial_entry)
        self.assertIsNone(section_entry)
    
    def test_multiple_instructors(self):
        section = {
            'type': 'LECT',
            'catalogNumber': '',
            'schedule': [],
            'meetNumber': '01',
            'instructors': ['John Doe', 'Jane Smith', '  ']  # Empty string should be filtered
        }
        
        _, _, _, instructor_links = process_single_section(section, 0, 'EECS1000')
        
        self.assertEqual(len(instructor_links), 2)
        self.assertIn(('John Doe', 'EECS1000'), instructor_links)
        self.assertIn(('Jane Smith', 'EECS1000'), instructor_links)


class TestProcessSections(unittest.TestCase):
    """Test process_sections function"""
    
    def setUp(self):
        # Create a course with index mapping
        self.course_code_to_index = {'EECS1000': 0}
        self.courses_list = [{'uuid': str(uuid.uuid4())}]
    
    def test_lab_section(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'sections': [{
                'type': 'LAB',
                'catalogNumber': 'L01',
                'schedule': [],
                'meetNumber': '01',
                'instructors': []
            }]
        }]
        
        labs, tutorials, sections, links = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(labs), 1)
        self.assertEqual(labs[0]['catalog_number'], 'L01')
        self.assertEqual(len(tutorials), 0)
        self.assertEqual(len(sections), 0)
    
    def test_tutorial_section(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'sections': [{
                'type': 'TUT',
                'catalogNumber': 'T01',
                'schedule': [],
                'meetNumber': '01',
                'instructors': []
            }]
        }]
        
        labs, tutorials, sections, links = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(tutorials), 1)
        self.assertEqual(tutorials[0]['catalog_number'], 'T01')
        self.assertEqual(len(labs), 0)
        self.assertEqual(len(sections), 0)
    
    def test_lecture_section(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'sections': [{
                'type': 'LECT',
                'catalogNumber': '',
                'schedule': [],
                'meetNumber': '01',
                'instructors': ['John Doe']
            }]
        }]
        
        labs, tutorials, sections, links = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]['letter'], '01')
        self.assertEqual(len(labs), 0)
        self.assertEqual(len(tutorials), 0)
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0], ('John Doe', 'EECS1000'))
    
    def test_instructor_course_links(self):
        courses = [{
            'department': 'EECS',
            'courseId': '1000',
            'sections': [{
                'type': 'LECT',
                'catalogNumber': '',
                'schedule': [],
                'meetNumber': '01',
                'instructors': ['John Doe', 'Jane Smith']
            }]
        }]
        
        _, _, _, links = process_sections(courses, self.course_code_to_index)
        
        self.assertEqual(len(links), 2)
        self.assertIn(('John Doe', 'EECS1000'), links)
        self.assertIn(('Jane Smith', 'EECS1000'), links)
    
    def test_unknown_course_code(self):
        courses = [{
            'department': 'MATH',
            'courseId': '9999',
            'sections': [{
                'type': 'LECT',
                'catalogNumber': '',
                'schedule': [],
                'meetNumber': '01',
                'instructors': []
            }]
        }]
        
        labs, tutorials, sections, links = process_sections(courses, self.course_code_to_index)
        
        # Should skip unknown course
        self.assertEqual(len(labs), 0)
        self.assertEqual(len(tutorials), 0)
        self.assertEqual(len(sections), 0)


class TestGenerateInstructorSQL(unittest.TestCase):
    """Test generate_instructor_sql function"""
    
    def test_single_instructor(self):
        instructors_map = {'John Doe': ('John', 'Doe')}
        sql_lines, instructor_name_to_uuid = generate_instructor_sql(instructors_map)
        
        self.assertGreater(len(sql_lines), 0)
        self.assertIn('-- Insert instructors', sql_lines)
        self.assertIn('INSERT INTO instructors', '\n'.join(sql_lines))
        self.assertIn('John', '\n'.join(sql_lines))
        self.assertEqual(len(instructor_name_to_uuid), 1)
        self.assertIn('John Doe', instructor_name_to_uuid)
    
    def test_multiple_instructors(self):
        instructors_map = {
            'John Doe': ('John', 'Doe'),
            'Jane Smith': ('Jane', 'Smith')
        }
        sql_lines, instructor_name_to_uuid = generate_instructor_sql(instructors_map)
        
        self.assertEqual(len(instructor_name_to_uuid), 2)
        self.assertIn('John Doe', instructor_name_to_uuid)
        self.assertIn('Jane Smith', instructor_name_to_uuid)
    
    def test_empty_instructors(self):
        sql_lines, instructor_name_to_uuid = generate_instructor_sql({})
        
        self.assertEqual(len(sql_lines), 1)  # Just the comment
        self.assertEqual(len(instructor_name_to_uuid), 0)


class TestGenerateCourseSQL(unittest.TestCase):
    """Test generate_course_sql function"""
    
    def test_single_course(self):
        courses_list = [{
            'uuid': str(uuid.uuid4()),
            'code': 'EECS1000',
            'name': 'Introduction to CS',
            'credits': 3.0,
            'description': 'Basic course'
        }]
        
        sql_lines = generate_course_sql(courses_list)
        
        self.assertIn('-- Insert courses', sql_lines)
        self.assertIn('INSERT INTO courses', '\n'.join(sql_lines))
        self.assertIn('EECS1000', '\n'.join(sql_lines))
        self.assertIn('Introduction to CS', '\n'.join(sql_lines))
    
    def test_course_with_null_description(self):
        courses_list = [{
            'uuid': str(uuid.uuid4()),
            'code': 'EECS1000',
            'name': 'Introduction to CS',
            'credits': 3.0,
            'description': ''
        }]
        
        sql_lines = generate_course_sql(courses_list)
        sql_content = '\n'.join(sql_lines)
        
        self.assertIn('NULL', sql_content)


class TestGenerateLabSQL(unittest.TestCase):
    """Test generate_lab_sql function"""
    
    def test_single_lab(self):
        course_uuid = str(uuid.uuid4())
        courses_list = [{'uuid': course_uuid}]
        labs_list = [{
            'course_idx': 0,
            'catalog_number': 'L01',
            'times': "'[{\"day\": \"M\"}]'"
        }]
        
        sql_lines = generate_lab_sql(labs_list, courses_list)
        
        self.assertIn('-- Insert labs', sql_lines)
        self.assertIn('INSERT INTO labs', '\n'.join(sql_lines))
        self.assertIn('L01', '\n'.join(sql_lines))
        self.assertIn(course_uuid, '\n'.join(sql_lines))
    
    def test_empty_labs(self):
        courses_list = []
        sql_lines = generate_lab_sql([], courses_list)
        
        self.assertEqual(len(sql_lines), 1)  # Just the comment


class TestGenerateTutorialSQL(unittest.TestCase):
    """Test generate_tutorial_sql function"""
    
    def test_single_tutorial(self):
        course_uuid = str(uuid.uuid4())
        courses_list = [{'uuid': course_uuid}]
        tutorials_list = [{
            'course_idx': 0,
            'catalog_number': 'T01',
            'times': "'[{\"day\": \"M\"}]'"
        }]
        
        sql_lines = generate_tutorial_sql(tutorials_list, courses_list)
        
        self.assertIn('-- Insert tutorials', sql_lines)
        self.assertIn('INSERT INTO tutorials', '\n'.join(sql_lines))
        self.assertIn('T01', '\n'.join(sql_lines))


class TestGenerateSectionSQL(unittest.TestCase):
    """Test generate_section_sql function"""
    
    def test_single_section(self):
        course_uuid = str(uuid.uuid4())
        courses_list = [{'uuid': course_uuid}]
        sections_list = [{
            'course_idx': 0,
            'lab_id': None,
            'letter': '01'
        }]
        
        sql_lines = generate_section_sql(sections_list, courses_list)
        
        self.assertIn('-- Insert sections', sql_lines)
        self.assertIn('INSERT INTO sections', '\n'.join(sql_lines))
        self.assertIn('01', '\n'.join(sql_lines))
        self.assertIn('NULL', '\n'.join(sql_lines))  # lab_id should be NULL
    
    def test_empty_sections(self):
        courses_list = []
        sql_lines = generate_section_sql([], courses_list)
        
        self.assertEqual(len(sql_lines), 1)  # Just the comment
        self.assertIn('-- Insert sections', sql_lines)


class TestGenerateJunctionTableSQL(unittest.TestCase):
    """Test generate_junction_table_sql function"""
    
    def test_single_link(self):
        instructor_uuid = str(uuid.uuid4())
        course_uuid = str(uuid.uuid4())
        instructor_course_links = [('John Doe', 'EECS1000')]
        instructor_name_to_uuid = {'John Doe': instructor_uuid}
        course_code_to_uuid = {'EECS1000': course_uuid}
        
        sql_lines = generate_junction_table_sql(
            instructor_course_links,
            instructor_name_to_uuid,
            course_code_to_uuid
        )
        
        self.assertIn('-- Insert instructor_courses junction table', sql_lines)
        self.assertIn('INSERT INTO instructor_courses', '\n'.join(sql_lines))
        self.assertIn(instructor_uuid, '\n'.join(sql_lines))
        self.assertIn(course_uuid, '\n'.join(sql_lines))
    
    def test_deduplication(self):
        instructor_uuid = str(uuid.uuid4())
        course_uuid = str(uuid.uuid4())
        # Same link twice
        instructor_course_links = [
            ('John Doe', 'EECS1000'),
            ('John Doe', 'EECS1000')
        ]
        instructor_name_to_uuid = {'John Doe': instructor_uuid}
        course_code_to_uuid = {'EECS1000': course_uuid}
        
        sql_lines = generate_junction_table_sql(
            instructor_course_links,
            instructor_name_to_uuid,
            course_code_to_uuid
        )
        
        sql_content = '\n'.join(sql_lines)
        # Should only appear once
        self.assertEqual(sql_content.count(instructor_uuid), 1)
    
    def test_empty_links(self):
        sql_lines = generate_junction_table_sql([], {}, {})
        
        self.assertEqual(len(sql_lines), 1)  # Just the comment


class TestGenerateSeedSQLIntegration(unittest.TestCase):
    """Integration test for generate_seed_sql function"""
    
    def setUp(self):
        self.test_json = {
            'courses': [
                {
                    'courseTitle': 'Test Course',
                    'department': 'TEST',
                    'courseId': '1000',
                    'credits': '3.00',
                    'notes': 'Test description',
                    'sections': [
                        {
                            'type': 'LECT',
                            'catalogNumber': '',
                            'schedule': [{'day': 'M', 'time': '10:00'}],
                            'meetNumber': '01',
                            'instructors': ['John Doe']
                        }
                    ]
                }
            ]
        }
    
    def test_full_generation(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as json_file:
            json.dump(self.test_json, json_file)
            json_path = json_file.name
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as sql_file:
                sql_path = sql_file.name
            
            try:
                generate_seed_sql(json_path, sql_path)
                
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
                self.assertIn('Test Course', content)
                # Name is parsed into first_name and last_name
                self.assertIn('John', content)
                self.assertIn('Doe', content)
                
            finally:
                if os.path.exists(sql_path):
                    os.unlink(sql_path)
        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)


if __name__ == '__main__':
    unittest.main()

