import unittest
import time
from typing import Dict
from gura_parser import GuraParser
import os
from parser import ParseError


class TestImportingGura(unittest.TestCase):
    file_dir: str
    parser: GuraParser
    expected: Dict

    def setUp(self):
        self.file_dir = os.path.dirname(os.path.abspath(__file__))
        self.parser = GuraParser()

        # All tests share the same content
        self.expected = {
            "from_file_one": 1,
            "from_file_two": {
                "name": "Aníbal",
                "surname": "Troilo",
                "year_of_birth": 1914
            },
            "from_original_1": [1, 2, 5],
            "from_original_2": False
        }

    def __get_file_parsed_data(self, file_name) -> Dict:
        """
        Gets the content of a specific file parsed
        :param file_name: File name to get the content
        :return: Parsed data
        """
        full_test_path = os.path.join(self.file_dir, f'tests-files/{file_name}')
        with open(full_test_path, 'r') as file:
            content = file.read()
        return self.parser.parse(content)

    def test_normal(self):
        """Tests importing from several files"""
        parsed_data = self.__get_file_parsed_data('normal.ura')
        self.assertDictEqual(parsed_data, self.expected)

    def test_not_found_error(self):
        """Tests errors importing a non existing file"""
        with self.assertRaises(ValueError):
            self.parser.parse(f'import "invalid_file.ura"')

    def test_duplicated_variables_error(self):
        """Tests errors when redefines a variable"""
        with self.assertRaises(ValueError):
            self.__get_file_parsed_data('duplicated_variables.ura')


if __name__ == '__main__':
    unittest.main()
