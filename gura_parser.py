import os
from typing import Dict, Any, Union, Optional, List, Set, Tuple
from parser import ParseError, Parser
from enum import Enum, auto


class DuplicatedImportError(Exception):
    """Raises when a file is imported more than once"""
    pass


class DuplicatedKeyError(Exception):
    """Raises when a key is defined more than once"""
    pass


class DuplicatedVariableError(Exception):
    """Raises when a variable is defined more than once"""
    pass


class VariableNotDefinedError(Exception):
    """Raises when a variable is not defined"""
    pass


# Number chars
BASIC_NUMBERS_CHARS = '0-9'
HEX_OCT_BIN = 'A-Fa-fxob'
INF_AND_NAN = 'in'  # The rest of the chars are defined in hex_oct_bin
# IMPORTANT: '-' char must be last, otherwise it will be interpreted as a range
ACCEPTABLE_NUMBER_CHARS = BASIC_NUMBERS_CHARS + HEX_OCT_BIN + INF_AND_NAN + 'Ee+._-'

# Acceptable chars for keys
KEY_ACCEPTABLE_CHARS = '0-9A-Za-z_-'


class MatchResultType(Enum):
    USELESS_LINE = auto(),
    PAIR = auto()
    COMMENT = auto()
    IMPORT = auto()
    VARIABLE = auto()


class MatchResult:
    result_type: MatchResultType
    value: Optional[Any]

    def __init__(self, result_type: MatchResultType, value: Optional[Any] = None):
        self.result_type = result_type
        self.value = value

    def __str__(self):
        return f'{self.result_type} -> {self.value}'


class GuraParser(Parser):
    variables: Dict[str, Any]
    indent_char: Optional[str]
    indentation_levels: List[int]
    imported_files: Set[str]

    def __init__(self):
        super(GuraParser, self).__init__()
        self.variables = {}
        self.indent_char = None
        self.indentation_levels = []
        self.imported_files = set()

    def parse(self, text):
        self.__restart_params(text)

        rv = self.start()

        self.assert_end()
        return rv if rv is not None else {}

    def __restart_params(self, text):
        """Sets the params to start parsing from a specific text"""
        self.text = text
        self.pos = -1
        self.line = 0
        self.len = len(text) - 1

    def new_line(self):
        res = self.char('\f\v\r\n')
        if res is not None:
            self.line += 1

    def comment(self):
        self.keyword('#')
        while self.pos < self.len:
            char = self.text[self.pos + 1]
            self.pos += 1
            if char in '\f\v\r\n':
                self.line += 1
                break
        print(f'Puntero en -> {self.text[self.pos]} (pos -> {self.pos})')
        return MatchResult(MatchResultType.COMMENT)

    def ws_with_indentation(self) -> int:
        """
        Matches with white spaces taking into consideration indentation levels
        @:return Indentation level
        """
        current_indentation_level = 0

        while self.pos < self.len:
            blank = self.maybe_keyword(' ', '\t')
            if blank is None:
                # If it is not a blank or new line, returns from the method
                break

            # If it is the first case of indentation stores the indentation char
            if self.indent_char is not None:
                # If user uses different kind of indentation raises a parsing error
                if blank != self.indent_char:
                    self.__raise_indentation_char_error()
            else:
                # From now on this character will be used to indicate the indentation
                self.indent_char = blank
            current_indentation_level += 1

        # TODO: add ParseError in case indentation is not divisible by 2
        return current_indentation_level

    def ws(self):
        """
        Matches white spaces and comments which start with '#'
        :return:
        """
        # TODO: refactor
        while True:
            blank = self.maybe_keyword(' ', '\t')
            if blank is None:
                break

    def eat_ws_and_new_lines(self):
        while self.maybe_char(' \f\v\r\n\t'):
            pass

    def __raise_indentation_char_error(self):
        """
        Raises a ParseError indicating that the indentation chars are inconsistent
        :raise: ParseError
        """
        if self.indent_char == '\t':
            good_char = 'tabs'
            received_char = 'whitespace'
        else:
            good_char = 'whitespace'
            received_char = 'tabs'
        raise ValueError(f'Wrong indentation character! Using {good_char} but received {received_char}')

    def get_text_with_imports(
        self,
        original_text,
        parent_dir_path: str,
        imported_files: Set[str]
    ) -> Tuple[str, Set[str]]:
        """
        Gets final text taking in consideration imports in original text
        :param original_text: Text to be parsed
        :param parent_dir_path: Parent directory to keep relative paths reference
        :param imported_files: Set with imported files to check if any was imported more than once
        :return: Final text with imported files' text on it
        """
        self.__restart_params(original_text)
        imported_files = self.__compute_imports(parent_dir_path, imported_files)
        return self.text, imported_files

    def gura_import(self) -> MatchResult:
        """Matches import sentence"""
        self.keyword('import')
        self.match('ws')
        file_to_import = self.match('quoted_string_with_var')
        self.match('ws')
        self.maybe_match('new_line')
        return MatchResult(MatchResultType.IMPORT, file_to_import)

    def quoted_string_with_var(self) -> str:
        """
        Matches with a quoted string (with a single quotation mark) taking into consideration a variable inside it.
        There is no special character escaping here
        :return: Matched string
        """
        quote = self.keyword('"')
        chars = []

        while True:
            char = self.char()

            if char == quote:
                break

            # Computes variables values in string
            if char == '$':
                var_name = self.__get_var_name()
                chars.append(self.__get_variable_value(var_name))
            else:
                chars.append(char)

        return ''.join(chars)

    def __get_var_name(self) -> str:
        """
        Gets a variable name char by char
        :return: Variable name
        """
        var_name = ''
        var_name_char = self.maybe_char(KEY_ACCEPTABLE_CHARS)
        while var_name_char is not None:
            var_name += var_name_char
            var_name_char = self.maybe_char(KEY_ACCEPTABLE_CHARS)
        return var_name

    def __compute_imports(self, parent_dir_path: Optional[str], imported_files: Set[str]) -> Set[str]:
        """
        Computes all the import sentences in Gura file taking into consideration relative paths to imported files
        :param parent_dir_path: Current parent directory path to join with imported files
        :param imported_files: Set with already imported files to raise an error in case of importing the same file
        more than once
        :return: Set with imported files after all the imports to reuse in the importation process of the imported
        Gura files
        """
        files_to_import: List[Tuple[str, str]] = []

        # First, consumes all the import sentences to replace all of them
        while self.pos < self.len:
            match_result: MatchResult = self.maybe_match('gura_import', 'variable', 'useless_line')
            if match_result is None:
                break

            # Checks, it could be a comment
            if match_result.result_type == MatchResultType.IMPORT:
                files_to_import.append((match_result.value, parent_dir_path))

        if len(files_to_import) > 0:
            final_content = ''
            for (file_to_import, origin_file_path) in files_to_import:
                # Gets the final file path considering parent directory
                if origin_file_path is not None:
                    file_to_import = os.path.join(origin_file_path, file_to_import)

                # Files can be imported only once. This prevents circular reference
                if file_to_import in imported_files:
                    raise DuplicatedImportError(f'The file {file_to_import} has been already imported')

                try:
                    with open(file_to_import, 'r') as f:
                        # Gets content considering imports
                        content = f.read()
                        aux_parser = GuraParser()
                        parent_dir_path = os.path.dirname(file_to_import)
                        content_with_import, imported_files = aux_parser.get_text_with_imports(
                            content,
                            parent_dir_path,
                            imported_files
                        )
                        final_content += content_with_import + '\n'
                        imported_files.add(file_to_import)

                        self.imported_files.add(file_to_import)
                except FileNotFoundError:
                    raise ValueError(f'The file {file_to_import} does not exist')

            # Sets as new text
            self.__restart_params(final_content + self.text[self.pos + 1:])
        return imported_files

    def start(self):
        self.__compute_imports(parent_dir_path=None, imported_files=set())
        rv = self.match('map')
        self.eat_ws_and_new_lines()
        return rv

    def any_type(self):
        rv = self.maybe_match('primitive_type')
        if rv is not None:
            return rv

        return self.match('complex_type')

    def primitive_type(self):
        self.maybe_match('ws')
        return self.match('null', 'boolean', 'basic_string', 'literal_string', 'number', 'variable_value')

    def complex_type(self):
        return self.match('list', 'map')

    def __get_variable_value(self, key: str) -> Any:
        """
        Gets a variable value for a specific key from defined variables in file or as environment variable
        :param key: Key to retrieve
        :return:
        :raise VariableNotDefinedError if the variable is not defined in file nor environment
        """
        if key in self.variables:
            return self.variables[key]

        env_variable = os.getenv(key)
        if env_variable is not None:
            return env_variable

        raise VariableNotDefinedError(f'Variable \'{key}\' is not defined in Gura nor as environment variable')

    def variable_value(self) -> Any:
        """Matches with an already defined variable and gets its value"""
        self.keyword('$')
        key = self.match('unquoted_string')
        return self.__get_variable_value(key)

    def variable(self):
        """Matches with a variable definition"""
        initial_pos = self.pos
        self.keyword('$')
        key = self.match('key')
        self.maybe_match('ws')
        value = self.match('any_type')

        if key in self.variables:
            raise DuplicatedVariableError(
                self.pos + 1,
                self.line,
                f'Variable \'{key}\' has been already declared',
            )

        # Store as variable
        self.variables[key] = value
        return MatchResult(MatchResultType.VARIABLE)

    def list(self):
        rv = []

        self.maybe_match('ws')
        self.keyword('[')
        while True:
            self.maybe_match('ws')
            self.maybe_match('new_line')

            # Discards useless lines between elements of array
            useless_line = self.maybe_match('useless_line')
            if useless_line is not None:
                continue

            item = self.maybe_match('any_type')
            print('ITEM ', item)
            if item is None:
                break

            rv.append(item)

            self.maybe_match('ws')
            if not self.maybe_keyword(','):
                break

        self.maybe_match('ws')
        self.maybe_match('new_line')
        self.keyword(']')
        return rv

    def useless_line(self):
        self.match('ws')
        comment = self.maybe_match('comment')
        initial_line = self.line
        self.maybe_match('new_line')
        is_new_line = (self.line - initial_line) == 1

        print(f'Comment -> {comment} | is_new_line -> {is_new_line}')
        if comment is None and not is_new_line:
            raise ParseError(
                self.pos + 1,
                self.line,
                f'It is a valid line',
            )

        return MatchResult(MatchResultType.USELESS_LINE)

    def map(self):
        rv = {}
        while self.pos < self.len:
            item: MatchResult = self.maybe_match('variable', 'pair', 'useless_line')

            if item is None:
                break

            if item.result_type == MatchResultType.PAIR:
                # It is a key/value pair
                key, value = item.value
                print(f"Pair obtenido '{item.value}'")
                if key in rv:
                    raise DuplicatedKeyError(
                        self.pos + 1,
                        self.line,
                        f'The key \'{key}\' has been already defined',
                    )

                rv[key] = value

            if self.maybe_keyword(']', ',') is not None:
                # Breaks if it is the end of a list
                self.__remove_last_indentation_level()
                self.pos -= 1
                break

        return rv if len(rv) > 0 else None

    def __remove_last_indentation_level(self):
        """Removes, if exists, the last indentation level"""
        if len(self.indentation_levels) > 0:
            self.indentation_levels.pop()

    def key(self):
        key = self.match('unquoted_string')
        print(f"Key encontrada -> '{key}'")
        if type(key) is not str:
            raise ParseError(
                self.pos + 1,
                self.line,
                'Expected string but got number',
                self.text[self.pos + 1]
            )

        self.keyword(':')
        return key

    def pair(self):
        pos_before_pair = self.pos
        current_indentation_level = self.maybe_match('ws_with_indentation')

        key = self.match('key')
        self.maybe_match('ws')
        self.maybe_match('new_line')

        # Check indentation
        last_indentation_block: Optional[int] = None if len(self.indentation_levels) == 0 \
            else self.indentation_levels[-1]
        print('current_indentation_level', current_indentation_level)
        print('last_indentation_block', last_indentation_block)
        if last_indentation_block is None or current_indentation_level > last_indentation_block:
            print(f'Agregando {current_indentation_level}')
            self.indentation_levels.append(current_indentation_level)
        elif current_indentation_level < last_indentation_block:
            print(f'Eliminando {last_indentation_block}')
            self.__remove_last_indentation_level()

            # As the indentation was consumed, it is needed to return to line beginning to get the indentation level
            # again in the previous matching. Otherwise, the other match would get indentation level = 0
            self.pos = pos_before_pair
            return None  # This breaks the parent loop

        value = self.match('any_type')
        print(f"Value encontrado -> '{value}'")
        self.maybe_match('new_line')

        return MatchResult(MatchResultType.PAIR, (key, value))

    def null(self) -> None:
        """
        Consumes null keyword and return None
        :return None
        """
        self.keyword('null')
        return None

    def boolean(self) -> bool:
        """
        Parses boolean values
        :return: Boolean value
        """
        return self.keyword('true', 'false') == 'true'

    def unquoted_string(self) -> str:
        """
        Parses an unquoted string. Useful for keys
        :return: Parsed unquoted string
        """
        chars = [self.char(KEY_ACCEPTABLE_CHARS)]

        while True:
            char = self.maybe_char(KEY_ACCEPTABLE_CHARS)
            if char is None:
                break

            chars.append(char)

        print("Retornando desde unquoted_string '" + ''.join(chars).rstrip(' \t') + "'")
        return ''.join(chars).rstrip(' \t')

    def number(self) -> Union[float, int, str]:
        """
        Parses a string checking if it is a number.
        :return: Returns an int, a float or a string depending of type inference
        """
        number_type = int

        print('number current char -> ', self.text[self.pos])
        chars = [self.char(ACCEPTABLE_NUMBER_CHARS)]

        while True:
            char = self.maybe_char(ACCEPTABLE_NUMBER_CHARS)
            if char is None:
                break

            if char in 'Ee.':
                number_type = float

            chars.append(char)

        rv = ''.join(chars).rstrip(' \t')

        # Checks hexadecimal and octal format
        prefix = rv[:2]
        if prefix in ['0x', '0o', '0b']:
            without_prefix = rv[2:]
            if prefix == '0x':
                base = 16
            elif prefix == '0o':
                base = 8
            else:
                base = 2
            return int(without_prefix, base)

        # Checks inf or NaN
        last_three_chars = rv[-3:]
        if last_three_chars in ['inf', 'nan']:
            return float(rv)

        try:
            print(f'RV en number -> {rv}')
            return number_type(rv)
        except ValueError:
            raise ParseError(
                self.pos + 1,
                self.line,
                f'\'{rv}\' is not a valid number',
            )

    def basic_string(self) -> str:
        """
        Matches with a simple/multiline basic string
        :return: Matched string
        """
        quote = self.keyword('"""', '"')

        is_multiline = quote == '"""'

        # NOTE:  A newline immediately following the opening delimiter will be trimmed. All other whitespace and
        # newline characters remain intact.
        if is_multiline:
            self.maybe_char('\n')

        chars = []

        escape_sequences = {
            'b': '\b',
            'f': '\f',
            'n': '\n',
            'r': '\r',
            't': '\t',
            '"': '"',
            '\\': '\\'
        }

        while True:
            closing_quote = self.maybe_keyword(quote)
            if closing_quote is not None:
                break

            char = self.char()
            if char == '\\':
                escape = self.char()

                # Checks backslash followed by a newline to trim all whitespaces
                if is_multiline and escape == '\n':
                    self.eat_ws_and_new_lines()
                # Supports Unicode of 16 and 32 bits representation
                elif escape == 'u' or escape == 'U':
                    num_chars_code_point = 4 if escape == 'u' else 8
                    code_point = []
                    for i in range(num_chars_code_point):
                        code_point.append(self.char('0-9a-fA-F'))
                    hex_value = int(''.join(code_point), 16)
                    chars.append(chr(hex_value))
                # Gets scaped char
                else:
                    chars.append(escape_sequences.get(escape, char))
            # Computes variables values in string
            elif char == '$':
                var_name = self.__get_var_name()
                chars.append(self.__get_variable_value(var_name))
            else:
                chars.append(char)

        return ''.join(chars)

    def literal_string(self) -> str:
        """
        Matches with a simple/multiline literal string
        :return: Matched string
        """
        quote = self.keyword("'''", "'")

        is_multiline = quote == "'''"

        # NOTE:  A newline immediately following the opening delimiter will be trimmed. All other whitespace and
        # newline characters remain intact.
        if is_multiline:
            self.maybe_char('\n')

        chars = []

        while True:
            closing_quote = self.maybe_keyword(quote)
            if closing_quote is not None:
                break

            char = self.char()
            chars.append(char)

        return ''.join(chars)


if __name__ == '__main__':
    from pprint import pprint

    parser = GuraParser()

    try:
        # pprint(parser.parse(sys.stdin.read()))
        with open('tests/prueba.ura', 'r') as file:
            parsed = parser.parse(file.read())
            pprint(parsed)
            print(parsed)
    except ParseError as e:
        print('Error: ', str(e))
