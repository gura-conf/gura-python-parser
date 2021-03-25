import unittest
from typing import Dict
from gura_parser import GuraParser
import os


class TestArraysGura(unittest.TestCase):
    file_dir: str
    parser: GuraParser
    expected_normal: Dict
    expected_object: Dict

    def setUp(self):
        self.file_dir = os.path.dirname(os.path.abspath(__file__))
        self.parser = GuraParser()

        # All tests share the same content
        self.expected_normal = {
            "integers": "test string",
            "int1": +99,
            "int2": 42,
            "int3": 0,
            "int4": -17,
            "int5": 1000,
            "int6": 5349221,
            "int7": 5349221
        }

        self.expected_object = {
            'testing': {
                'test_2': 2,
                'test': {
                    'name': 'JWARE',
                    'surname': 'Solutions'
                }
            }
        }

        self.expected_object_complex = {
            'testing': {
                'test': {
                    'name': 'JWARE',
                    'surname': 'Solutions',
                    'skills': {
                        'good_testing': False,
                        'good_programming': False,
                        'good_english': False
                    }
                },
                'test_2': 2,
                'test_3': {
                    'key_1': True,
                    'key_2': False,
                    'key_3': 55.99
                }
            }
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
        """Tests all kind of arrays"""
        parsed_data = self.__get_file_parsed_data('normal.ura')
        self.assertDictEqual(parsed_data, self.expected_normal)

    def test_with_comments(self):
        """Tests all kind of arrays with comments between elements"""
        parsed_data = self.__get_file_parsed_data('with_comments.ura')
        self.assertDictEqual(parsed_data, self.expected_normal)


if __name__ == '__main__':
    unittest.main()
