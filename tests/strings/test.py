import time
import unittest
from typing import Dict
from gura_parser import GuraParser, VariableNotDefinedError
import os


class TestStringsGura(unittest.TestCase):
    file_dir: str
    parser: GuraParser
    expected_basic: Dict
    expected_multiline_basic: Dict

    def setUp(self):
        self.file_dir = os.path.dirname(os.path.abspath(__file__))
        self.parser = GuraParser()

        self.expected_basic = {
            "str": "I'm a string. \"You can quote me\". Na\bme\tJos\u00E9\nLocation\tSF.",
            "str_2": "I'm a string. \"You can quote me\". Na\bme\tJos\U000000E9\nLocation\tSF.",
            "with_var": "Gura is cool",
            "with_env_var": "Gura is very cool"
        }

        multiline_value = "Roses are red\nViolets are blue"
        self.expected_multiline_basic = {
            "str": multiline_value,
            "str_2": multiline_value,
            "str_3": multiline_value,
            "with_var": multiline_value,
            "with_env_var": multiline_value
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

    def test_basic_strings(self):
        """Tests basic strings"""
        env_var_name = 'env_var_value'
        os.environ[env_var_name] = 'very'
        parsed_data = self.__get_file_parsed_data('basic.ura')
        os.unsetenv(env_var_name)
        self.assertDictEqual(parsed_data, self.expected_basic)

    def test_multiline_basic_strings(self):
        """Tests multiline basic strings"""
        env_var_name = 'env_var_value'
        os.environ[env_var_name] = 'Roses'
        parsed_data = self.__get_file_parsed_data('multiline_basic.ura')
        os.unsetenv(env_var_name)
        self.assertDictEqual(parsed_data, self.expected_multiline_basic)

    def test_basic_strings_errors(self):
        """Tests errors in basic strings"""
        with self.assertRaises(VariableNotDefinedError):
            self.parser.parse(f'test: "$false_var_{time.time_ns()}"')


if __name__ == '__main__':
    unittest.main()