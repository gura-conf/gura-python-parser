import unittest
from typing import Dict
from gura import DuplicatedImportError, DuplicatedKeyError, DuplicatedVariableError, ParseError, \
    InvalidIndentationError, VariableNotDefinedError
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
        :param exception: Expected exception type
        :param error_pos: Error position
        :param error_line: Error line
        """
        try:
            self.__get_file_parsed_data(filename)
            self.fail(f'Expected to raise {exception}')
        except exception as e:
            self.assertEqual(e.pos, error_pos)
            self.assertEqual(e.line, error_line)
        except Exception as e:
            self.fail(f'Expected to raise {exception}, raised {type(e)} with message: "{e}"')

    def test_line_and_pos_1(self):
        """Tests error position and line at beginning"""
        self.__test_fail('parsing_error_1.ura', ParseError, error_pos=0, error_line=1)

    def test_line_and_pos_2(self):
        """Tests error position and line at the end of file"""
        self.__test_fail('parsing_error_2.ura', ParseError, error_pos=10, error_line=1)

    def test_line_and_pos_3(self):
        """Tests error position and line in some random line"""
        self.__test_fail('parsing_error_3.ura', ParseError, error_pos=42, error_line=2)

    def test_line_and_pos_4(self):
        """Tests error position and line in some random line"""
        self.__test_fail('parsing_error_4.ura', ParseError, error_pos=45, error_line=6)

    def test_line_and_pos_indentation_1(self):
        """Tests error position and line when user uses tabs to indent"""
        self.__test_fail('indentation_error_1.ura', InvalidIndentationError, error_pos=20, error_line=3)

    def test_line_and_pos_indentation_2(self):
        """Tests error position and line when indentation is not divisible by 4"""
        self.__test_fail('indentation_error_2.ura', InvalidIndentationError, error_pos=19, error_line=3)

    def test_line_and_pos_indentation_3(self):
        """Tests error position and line when pair indentation is the same as the the parent"""
        self.__test_fail('indentation_error_3.ura', InvalidIndentationError, error_pos=18, error_line=3)

    def test_line_and_pos_indentation_4(self):
        """Tests error position and line when pair indentation is more than 4 spaces from parent indentation level"""
        self.__test_fail('indentation_error_4.ura', InvalidIndentationError, error_pos=26, error_line=3)

    def test_duplicated_key_1(self):
        """Tests error position and line when user defines the same key twice"""
        self.__test_fail('duplicated_key_error_1.ura', DuplicatedKeyError, error_pos=11, error_line=2)

    def test_duplicated_key_2(self):
        """Tests error position and line when user defines the same key twice but in other line than 0"""
        self.__test_fail('duplicated_key_error_2.ura', DuplicatedKeyError, error_pos=21, error_line=3)

    def test_duplicated_key_3(self):
        """Tests error position and line when user defines the same key twice inside an object"""
        self.__test_fail('duplicated_key_error_3.ura', DuplicatedKeyError, error_pos=37, error_line=4)

    def test_duplicated_variable_1(self):
        """Tests error position and line when user defines the same variable twice inside an object"""
        self.__test_fail('duplicated_variable_error_1.ura', DuplicatedVariableError, error_pos=12, error_line=2)

    def test_duplicated_variable_2(self):
        """Tests error position and line when user defines the same variable twice but in other line than 0"""
        self.__test_fail('duplicated_variable_error_2.ura', DuplicatedVariableError, error_pos=25, error_line=3)

    def test_duplicated_variable_3(self):
        """Tests error position and line when user defines the same variable twice but in other line than 0"""
        self.__test_fail('duplicated_variable_error_3.ura', DuplicatedVariableError, error_pos=37, error_line=6)

    def test_missing_variable_1(self):
        """Tests error position and line when user uses a non defined variable"""
        self.__test_fail('missing_variable_error_1.ura', VariableNotDefinedError, error_pos=5, error_line=1)

    def test_missing_variable_2(self):
        """Tests error position and line when user uses a non defined variable but in other line than 0"""
        self.__test_fail('missing_variable_error_2.ura', VariableNotDefinedError, error_pos=19, error_line=2)

    def test_missing_variable_3(self):
        """Tests error position and line when user uses a non defined variable but in other line than 0"""
        self.__test_fail('missing_variable_error_3.ura', VariableNotDefinedError, error_pos=33, error_line=7)

    def test_missing_variable_4(self):
        """Tests error position and line when user uses a non defined variable inside a basic string"""
        self.__test_fail('missing_variable_error_4.ura', VariableNotDefinedError, error_pos=17, error_line=1)

    def test_missing_variable_5(self):
        """Tests error position and line when user uses a non defined variable inside a multiline basic string"""
        self.__test_fail('missing_variable_error_5.ura', VariableNotDefinedError, error_pos=24, error_line=2)

    def test_missing_variable_6(self):
        """Tests error position and line when user uses a non defined variable inside an import statement"""
        self.__test_fail('missing_variable_error_6.ura', VariableNotDefinedError, error_pos=21, error_line=1)

    def test_duplicated_import_1(self):
        """Tests error position and line when imported files are duplicated"""
        self.__test_fail('importing_error_1.ura', DuplicatedImportError, error_pos=74, error_line=2)
        
    def test_duplicated_import_2(self):
        """Tests error position and line when imported files are duplicated but in other line than 0"""
        self.__test_fail('importing_error_2.ura', DuplicatedImportError, error_pos=86, error_line=5)


if __name__ == '__main__':
    unittest.main()
