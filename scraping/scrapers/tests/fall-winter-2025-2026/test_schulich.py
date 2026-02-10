"""Test cases for schulich.py scraper"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, mock_open
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraping.scrapers import schulich


class TestSchulichIntegration(unittest.TestCase):
    """Integration tests for schulich scraper"""
    
    def test_main_with_missing_html_file(self):
        """Test main function handles missing HTML file gracefully"""
        with patch('pathlib.Path.read_text', side_effect=FileNotFoundError("File not found")), \
             patch('builtins.print') as mock_print:
            schulich.main()
            # Should print error message
            call_args = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any('Error reading HTML' in arg for arg in call_args))
    
    def test_main_with_valid_html(self):
        """Test main function with valid HTML"""
        test_html = """
        <html>
            <body>
                <table>
                    <tr>
                        <td class="bodytext">SU</td>
                        <td class="bodytext">ACTG</td>
                        <td class="bodytext">FW25</td>
                        <td class="bodytext" colspan="6">Accounting Basics</td>
                    </tr>
                    <tr>
                        <td>2000 3.00 A</td>
                        <td>EN</td>
                        <td>LEC</td>
                        <td>01</td>
                        <td>A01</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        with patch('pathlib.Path.read_text', return_value=test_html), \
             patch('pathlib.Path.write_text') as mock_write, \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.print') as mock_print:
            
            schulich.main()
            
            # Verify write was called
            self.assertTrue(mock_write.called)
            
            # Verify success message was printed
            call_args = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any('Saved' in arg for arg in call_args))
    
    def test_main_with_parsing_error(self):
        """Test main function handles parsing errors"""
        invalid_html = "<html><invalid></html>"
        
        with patch('pathlib.Path.read_text', return_value=invalid_html), \
             patch('pathlib.Path.write_text'), \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.print') as mock_print:
            
            schulich.main()
            
            # Should complete without crashing
            self.assertTrue(mock_print.called)

    def test_main_uses_correct_parameters(self):
        """Test that main uses correct parser parameters"""
        test_html = "<table></table>"
        
        with patch('pathlib.Path.read_text', return_value=test_html), \
            patch('pathlib.Path.write_text'), \
            patch('pathlib.Path.mkdir'), \
            patch('scraping.scrapers.schulich.parse_course_timetable_html') as mock_parse, \
            patch('builtins.print'):
            
            mock_parse.return_value = {'courses': []}
            schulich.main()
            
            # Verify parser was called with correct parameters
            mock_parse.assert_called_once()
            call_kwargs = mock_parse.call_args[1]
            self.assertEqual(call_kwargs['extract_metadata'], False)
            self.assertNotIn('allow_alphanumeric_course_id', call_kwargs)

    def test_main_with_json_serialization_error(self):
        """Test main function handles JSON serialization errors"""
        test_html = "<table></table>"
        
        with patch('pathlib.Path.read_text', return_value=test_html), \
            patch('pathlib.Path.mkdir'), \
            patch('scraping.scrapers.schulich.parse_course_timetable_html') as mock_parse, \
            patch('pathlib.Path.write_text', side_effect=Exception("Write error")), \
            patch('builtins.print') as mock_print, \
            patch('traceback.print_exc') as mock_traceback:
            
            mock_parse.return_value = {'courses': []}
            schulich.main()
            
            # Verify error was printed
            call_args = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any('Error parsing HTML' in arg for arg in call_args))
            
            # Verify traceback was printed
            self.assertTrue(mock_traceback.called)

    def test_main_with_parser_exception(self):
        """Test main function handles parser exceptions with traceback"""
        test_html = "<table></table>"
        
        with patch('pathlib.Path.read_text', return_value=test_html), \
            patch('pathlib.Path.mkdir'), \
            patch('scraping.scrapers.schulich.parse_course_timetable_html', side_effect=ValueError("Parse error")), \
            patch('builtins.print') as mock_print, \
            patch('traceback.print_exc') as mock_traceback:
            
            schulich.main()
            
            # Verify error handling
            call_args = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any('Error parsing HTML' in arg for arg in call_args))
            self.assertTrue(mock_traceback.called)

    def test_main_prints_course_details(self):
        """Test main function prints course details"""
        test_html = "<table></table>"
        
        mock_result = {
            'courses': [
                {
                    'courseId': '2000',
                    'courseTitle': 'Accounting Basics',
                    'sections': [
                        {'section': 'A', 'type': 'LECT'},
                        {'section': 'B', 'type': 'LECT'}
                    ]
                }
            ]
        }
        
        with patch('pathlib.Path.read_text', return_value=test_html), \
            patch('pathlib.Path.write_text'), \
            patch('pathlib.Path.mkdir'), \
            patch('scraping.scrapers.schulich.parse_course_timetable_html', return_value=mock_result), \
            patch('builtins.print') as mock_print:
            
            schulich.main()
            
            # Verify course details were printed
            call_args = str(mock_print.call_args_list)
            self.assertIn('2000', call_args)
            self.assertIn('Accounting Basics', call_args)
            self.assertIn('Section', call_args)


if __name__ == '__main__':
    unittest.main()
