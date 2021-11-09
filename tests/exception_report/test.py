import unittest
from typing import Dict
from gura import DuplicatedImportError, DuplicatedKeyError, DuplicatedVariableError, ParseError, InvalidIndentationError
import gura
import os

from gura.Parser import GuraError


class TestExceptionReportGura(unittest.TestCase):
    file_dir: str
    expected: Dict

    def setUp(self):
        self.file_dir = os.path.dirname(os.path.abspath(__file__))

    def __get_file_parsed_data(self, file_name) -> Dict:
        """
        Gets the content of a specific file parsed
        :param file_name: File name to get the content
        :return: Parsed data
        """
        full_test_path = os.path.join(self.file_dir, f'tests-files/{file_name}')
        with open(full_test_path, 'r') as file:
            content = file.read()
        return gura.loads(content)

    def __test_fail(self, filename: str, exception: GuraError, error_pos: int, error_line: int):
        """
        Test error position and line of a specific file
        :param filename: File path to check
        :param error_pos: Error position
        :param error_line: Error line
        """
        try:
            self.__get_file_parsed_data(filename)
        except exception as e:
            self.assertEqual(e.pos, error_pos)
            self.assertEqual(e.line, error_line)
        except Exception as e:
            self.fail(f'Expected to raise {exception}, raised {type(e)} with message: "{e}"')

    def test_line_and_pos_1(self):
        """Tests error position and line at beginning"""
        self.__test_fail('parsing_error_1.ura', ParseError, error_pos=0, error_line=0)

    def test_line_and_pos_2(self):
        """Tests error position and line at end"""
        self.__test_fail('parsing_error_2.ura', ParseError, error_pos=10, error_line=0)

    def test_line_and_pos_3(self):
        """Tests error position and line in some random line"""
        self.__test_fail('parsing_error_3.ura', ParseError, error_pos=42, error_line=1)

    def test_line_and_pos_4(self):
        """Tests error position and line in some random line"""
        self.__test_fail('parsing_error_4.ura', ParseError, error_pos=46, error_line=5)

    # def test_line_and_pos_5(self):
    #     """Tests error position and line when user uses tabs to indent"""
    #     self.__test_fail('indentation_error_1.ura', InvalidIndentationError, error_pos=20, error_line=2)

    # def test_line_and_pos_6(self):
    #     """Tests error position and line when imported files are duplicated"""
    #     self.__test_fail('importing_error_1.ura', DuplicatedImportError, error_pos=20, error_line=2)


if __name__ == '__main__':
    unittest.main()
