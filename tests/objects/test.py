import unittest
from typing import Dict
import gura
from gura import InvalidIndentationError, ParseError
import os


class TestObjectsGura(unittest.TestCase):
    file_dir: str
    expected: Dict
    empty_object: Dict

    def setUp(self):
        self.file_dir = os.path.dirname(os.path.abspath(__file__))

        # All tests share the same content
        self.expected = {
            "user1": {
                "name": "Carlos",
                "surname": "Gardel",
                "testing_nested": {
                    "nested_1": 1,
                    "nested_2": 2
                },
                "year_of_birth": 1890
            },
            "user2": {
                "name": "Aníbal",
                "surname": "Troilo",
                "year_of_birth": 1914
            }
        }

        self.empty_object = {
            'empty_object': {}
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
        return gura.loads(content)

    def test_normal(self):
        """Tests all kind of objects"""
        parsed_data = self.__get_file_parsed_data('normal.ura')
        self.assertDictEqual(parsed_data, self.expected)

    def test_empty(self):
        """Tests empty object"""
        parsed_data = gura.loads('empty_object: empty')
        self.assertDictEqual(parsed_data, self.empty_object)

    def test_empty_2(self):
        """Tests empty object with several blanks"""
        parsed_data = gura.loads('empty_object:     empty    ')
        self.assertDictEqual(parsed_data, self.empty_object)

    def test_empty_3(self):
        """Tests empty object with comments and blank lines"""
        parsed_data = self.__get_file_parsed_data('empty.ura')
        self.assertDictEqual(parsed_data, self.empty_object)

    def test_with_comments(self):
        """Tests all kind of objects with comments between elements"""
        parsed_data = self.__get_file_parsed_data('with_comments.ura')
        self.assertDictEqual(parsed_data, self.expected)

    def test_invalid(self):
        """Tests parsing error in invalid objects"""
        with self.assertRaises(ParseError):
            self.__get_file_parsed_data('invalid.ura')

    def test_invalid_2(self):
        """Tests parsing error in invalid objects"""
        with self.assertRaises(InvalidIndentationError):
            self.__get_file_parsed_data('invalid_2.ura')

    def test_invalid_3(self):
        """Tests parsing error in invalid objects"""
        with self.assertRaises(ParseError):
            self.__get_file_parsed_data('invalid_3.ura')


if __name__ == '__main__':
    unittest.main()
