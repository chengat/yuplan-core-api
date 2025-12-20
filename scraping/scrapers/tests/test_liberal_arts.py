"""Test cases for liberal_arts.py scraper"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, mock_open
import json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scraping.scrapers import liberal_arts


class TestSchoolOfArtsIntegration(unittest.TestCase):
    """Integration tests for liberal_arts scraper"""
    
    def test_main_with_missing_html_file(self):
        """Test main function handles missing HTML file gracefully"""
        with patch('pathlib.Path.read_text', side_effect=FileNotFoundError("File not found")), \
             patch('builtins.print') as mock_print:
            liberal_arts.main()
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
                        <td class="bodytext">Faculty of Science</td>
                        <td class="bodytext">EECS</td>
                        <td class="bodytext">FW 2024</td>
                        <td class="bodytext" colspan="2">Introduction to Programming</td>
                    </tr>
                    <tr>
                        <td>1000 3.00</td>
                        <td>EN</td>
                        <td>LECT</td>
                        <td>01</td>
                        <td>A</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        
        with patch('pathlib.Path.read_text', return_value=test_html), \
             patch('pathlib.Path.write_text') as mock_write, \
             patch('pathlib.Path.mkdir'), \
             patch('builtins.print') as mock_print:
            
            liberal_arts.main()
            
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
            
            liberal_arts.main()
            
            # Should complete without crashing
            self.assertTrue(mock_print.called)

    def test_main_uses_correct_parameters(self):
        """Test that main uses correct parser parameters"""
        test_html = "<table></table>"
        
        with patch('pathlib.Path.read_text', return_value=test_html), \
            patch('pathlib.Path.write_text'), \
            patch('pathlib.Path.mkdir'), \
            patch('scraping.scrapers.liberal_arts.parse_course_timetable_html') as mock_parse, \
            patch('builtins.print'):
            
            mock_parse.return_value = {'courses': []}
            liberal_arts.main()
            
            # Verify parser was called with correct parameters
            mock_parse.assert_called_once()
            call_kwargs = mock_parse.call_args[1]
            self.assertEqual(call_kwargs['extract_metadata'], True)
            self.assertEqual(call_kwargs['allow_alphanumeric_course_id'], False)

    def test_main_with_json_serialization_error(self):
        """Test main function handles JSON serialization errors"""
        test_html = "<table></table>"
        
        with patch('pathlib.Path.read_text', return_value=test_html), \
            patch('pathlib.Path.mkdir'), \
            patch('scraping.scrapers.liberal_arts.parse_course_timetable_html') as mock_parse, \
            patch('pathlib.Path.write_text', side_effect=Exception("Write error")), \
            patch('builtins.print') as mock_print, \
            patch('traceback.print_exc') as mock_traceback:
            
            mock_parse.return_value = {'courses': []}
            liberal_arts.main()
            
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
            patch('scraping.scrapers.liberal_arts.parse_course_timetable_html', side_effect=ValueError("Parse error")), \
            patch('builtins.print') as mock_print, \
            patch('traceback.print_exc') as mock_traceback:
            
            liberal_arts.main()
            
            # Verify error handling
            call_args = [str(call) for call in mock_print.call_args_list]
            self.assertTrue(any('Error parsing HTML' in arg for arg in call_args))
            self.assertTrue(mock_traceback.called)


if __name__ == '__main__':
    unittest.main()