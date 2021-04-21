import unittest
from typing import Dict
from gura_parser import GuraParser, InvalidIndentationError
import os


class TestIndentationGura(unittest.TestCase):
    file_dir: str
    parser: GuraParser
    expected: Dict
    expected_object: Dict

    def setUp(self):
        self.file_dir = os.path.dirname(os.path.abspath(__file__))
        self.parser = GuraParser()

    def __get_file_parsed_data(self, file_name) -> Dict:
        """
        Gets the content of a specific file parsed
        :param file_name: File name to get the content
        :return: Parsed data
        """
        full_test_path = os.path.join(self.file_dir, f'tests-files/{file_name}')
        with open(full_test_path, 'r') as file:
            content = file.read()
        return self.parser.loads(content)

    def test_wrong_indentation_char(self):
        """Tests raising an error when both whitespace and tabs are used at the time for indentation"""
        with self.assertRaises(InvalidIndentationError):
            self.__get_file_parsed_data('different_chars.ura')

    def test_indentation_not_divisible_by_2(self):
        """Tests raising an error when indentation is not divisible by 2"""
        with self.assertRaises(InvalidIndentationError):
            self.__get_file_parsed_data('not_divisible_by_2.ura')


if __name__ == '__main__':
    unittest.main()
