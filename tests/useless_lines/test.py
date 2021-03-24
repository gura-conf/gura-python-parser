import unittest
from typing import Dict
from gura_parser import GuraParser
import os


class TestFullGura(unittest.TestCase):
    file_dir: str
    parser: GuraParser
    expected: Dict

    def setUp(self):
        self.file_dir = os.path.dirname(os.path.abspath(__file__))
        self.parser = GuraParser()

        # All tests share the same content
        self.expected = {
            "a_string": "test string",
            "int1": +99,
            "int2": 42,
            "int3": 0,
            "int4": -17,
            "int5": 1000,
            "int6": 5349221,
            "int7": 5349221
        }

    def __check_test_file(self, file_name: str):
        """
        Gets the content of a specific file parsed and tests it against the expected data
        :param file_name: File name to get the content and test
        """
        full_test_path = os.path.join(self.file_dir, f'tests-files/{file_name}')
        with open(full_test_path, 'r') as file:
            content = file.read()
        parsed_data = self.parser.parse(content)
        self.assertDictEqual(parsed_data, self.expected)

    def test_without(self):
        """Tests without comments or blank lines"""
        self.__check_test_file('without.ura')

    def test_on_top(self):
        """Tests with comments or blank lines on the top of the file"""
        self.__check_test_file('on_top.ura')

    def test_on_bottom(self):
        """Tests with comments or blank lines on the bottom of the file"""
        self.__check_test_file('on_bottom.ura')

    def test_on_both(self):
        """Tests with comments or blank lines on the top and bottom of the file"""
        self.__check_test_file('on_both.ura')

    def test_in_the_middle(self):
        """Tests with comments or blank lines in the middle of valid sentences"""
        self.__check_test_file('in_the_middle.ura')


if __name__ == '__main__':
    unittest.main()
