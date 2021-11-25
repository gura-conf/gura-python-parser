import os
from typing import Dict, Any, Optional, List, Set, Tuple
from gura.Parser import ParseError, Parser, GuraError
from enum import Enum, auto


class DuplicatedImportError(GuraError):
    """Raises when a file is imported more than once"""
    pass


class DuplicatedKeyError(GuraError):
    """Raises when a key is defined more than once"""
    pass


class DuplicatedVariableError(GuraError):
    """Raises when a variable is defined more than once"""
    pass


class VariableNotDefinedError(GuraError):
    """Raises when a variable is not defined"""
    pass


class InvalidIndentationError(GuraError):
    """Raises when indentation is invalid"""
    pass


# Number chars
BASIC_NUMBERS_CHARS = '0-9'
HEX_OCT_BIN = 'A-Fa-fxob'
INF_AND_NAN = 'in'  # The rest of the chars are defined in hex_oct_bin
# IMPORTANT: '-' char must be last, otherwise it will be interpreted as a range
ACCEPTABLE_NUMBER_CHARS = BASIC_NUMBERS_CHARS + HEX_OCT_BIN + INF_AND_NAN + 'Ee+._-'

# Acceptable chars for keys
KEY_ACCEPTABLE_CHARS = '0-9A-Za-z_'

# Special characters to be escaped when parsing values
ESCAPE_SEQUENCES = {
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
    '"': '"',
    '\\': '\\',
    '$': '$'
}

# Sequences that need escaped when dumping string values
SEQUENCES_TO_ESCAPE = {
    '\\': '\\\\',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
    '"': '\\"',
    '$': '\\$',
}

# Indentation of 4 spaces
INDENT = '    '


class MatchResultType(Enum):
    USELESS_LINE = auto(),
    PAIR = auto()
    COMMENT = auto()
    IMPORT = auto()
    VARIABLE = auto()
    LIST = auto()
    EXPRESSION = auto()
    PRIMITIVE = auto()


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
    indentation_levels: List[int]
    imported_files: Set[str]

    def __init__(self):
        super(GuraParser, self).__init__()
        self.variables = {}
        self.indentation_levels = []
        self.imported_files = set()

    def loads(self, text: str) -> Dict:
        """
        Parses a text in Gura format
        :param text: Text to be parsed
        :raise: ParseError if the syntax of text is invalid
        :return: Dict with all the parsed values
        """
        self.__restart_params(text)
        result = self.start()
        self.assert_end()
        return result if result is not None else {}

    def __restart_params(self, text: str):
        """
        Sets the params to start parsing from a specific text
        :param text: Text to set as the internal text to be parsed
        """
        self.text = text
        self.pos = -1
        self.line = 1
        self.len = len(text) - 1

    def new_line(self):
        """Matches with a new line"""
        self.char('\f\v\r\n')
        self.line += 1  # If this line is reached then new line matched

    def comment(self) -> MatchResult:
        """
        Matches with a comment
        :return: MatchResult indicating the presence of a comment
        """
        self.keyword('#')
        while self.pos < self.len:
            char = self.text[self.pos + 1]
            self.pos += 1
            if char in '\f\v\r\n':
                self.line += 1
                break

        return MatchResult(MatchResultType.COMMENT)

    def ws_with_indentation(self) -> int:
        """
        Matches with white spaces taking into consideration indentation levels
        :return Indentation level
        """
        current_indentation_level = 0

        while self.pos < self.len:
            blank = self.maybe_keyword(' ', '\t')
            if blank is None:
                # If it is not a blank or new line, returns from the method
                break

            # Tabs are not allowed
            if blank == '\t':
                raise InvalidIndentationError(
                    self.pos,
                    self.line,
                    'Tabs are not allowed to define indentation blocks'
                )

            current_indentation_level += 1

        return current_indentation_level

    def ws(self):
        """Matches white spaces (blanks and tabs)"""
        while self.maybe_keyword(' ', '\t') is not None:
            pass

    def eat_ws_and_new_lines(self):
        """Consumes all the whitespaces and new lines"""
        while self.maybe_char(' \f\v\r\n\t'):
            pass

    def get_text_with_imports(self, original_text: str, parent_dir_path: str) -> str:
        """
        Gets final text taking in consideration imports in original text
        :param original_text: Text to be parsed
        :param parent_dir_path: Parent directory to keep relative paths reference
        :return: Final text with imported files' text on it
        """
        self.__restart_params(original_text)
        self.__compute_imports(parent_dir_path)
        return self.text

    def gura_import(self) -> MatchResult:
        """Matches import sentence"""
        self.keyword('import')
        self.char(' ')
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
                initial_pos = self.pos
                initial_line = self.line
                var_name = self.__get_var_name()
                chars.append(self.__get_variable_value(var_name, initial_pos, initial_line))
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

    def __compute_imports(self, parent_dir_path: Optional[str]):
        """
        Computes all the import sentences in Gura file taking into consideration relative paths to imported files
        :param parent_dir_path: Current parent directory path to join with imported files
        more than once
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
                if file_to_import in self.imported_files:
                    raise DuplicatedImportError(
                        self.pos - len(file_to_import) - 1,  # -1 for the quotes (")
                        self.line,
                        f'The file "{file_to_import}" has been already imported'
                    )

                with open(file_to_import, 'r') as f:
                    # Gets content considering imports
                    content = f.read()
                    aux_parser = GuraParser()
                    parent_dir_path = os.path.dirname(file_to_import)
                    content_with_import = aux_parser.get_text_with_imports(content, parent_dir_path)
                    final_content += content_with_import + '\n'

                    self.imported_files.add(file_to_import)

            # Sets as new text
            self.__restart_params(final_content + self.text[self.pos + 1:])

    def start(self) -> Dict:
        """
        Computes imports and matches the first expression of the file. Finally consumes all the useless lines
        :return: Dict with all the extracted values from Gura string
        """
        self.__compute_imports(parent_dir_path=None)
        result: Optional[MatchResult] = self.match('expression')
        self.eat_ws_and_new_lines()
        return result.value[0] if result is not None else None

    def any_type(self) -> Any:
        """
        Matches with any primitive or complex type
        :return: The corresponding matched value
        """
        result: Optional[MatchResult] = self.maybe_match('primitive_type')
        if result is not None:
            return result

        return self.match('complex_type')

    def primitive_type(self):
        """
        Matches with a primitive value: null, bool, strings (all of the four kind of string), number or variables values
        :return: The corresponding matched value
        """
        self.maybe_match('ws')
        result = self.match('null', 'boolean', 'basic_string', 'literal_string', 'number', 'variable_value',
                            'empty_object')
        self.maybe_match('ws')
        return result

    def complex_type(self) -> Optional[Tuple[List, Dict]]:
        """
        Matches with a list or another complex expression
        :return: List or Dict, depending the correct matching
        """
        return self.match('list', 'expression')

    def __get_variable_value(self, key: str, position: int, line: int) -> Any:
        """
        Gets a variable value for a specific key from defined variables in file or as environment variable
        :param key: Key to retrieve
        :param position: Current position to report Exception (if needed)
        :param line: Current line to report Exception (if needed)
        :raise VariableNotDefinedError if the variable is not defined in file nor environment
        :return: Variable value
        """
        if key in self.variables:
            return self.variables[key]

        env_variable = os.getenv(key)
        if env_variable is not None:
            return env_variable

        raise VariableNotDefinedError(
            position,
            line,
            f'Variable "{key}" is not defined in Gura nor as environment variable'
        )

    def variable_value(self) -> MatchResult:
        """
        Matches with an already defined variable and gets its value
        :return: Variable value
        """
        self.keyword('$')
        key = self.match('unquoted_string')
        pos = self.pos - len(key)
        line = self.line
        return MatchResult(MatchResultType.PRIMITIVE, self.__get_variable_value(key, pos, line))

    def variable(self) -> MatchResult:
        """
        Matches with a variable definition
        :raise: DuplicatedVariableError if the current variable has been already defined
        :return: Match result indicating that a variable has been added
        """
        initial_pos = self.pos
        initial_line = self.line

        self.keyword('$')
        key = self.match('key')
        self.maybe_match('ws')
        match_result: MatchResult = self.match('basic_string', 'literal_string', 'number', 'variable_value')

        if key in self.variables:
            raise DuplicatedVariableError(
                initial_pos + 1,
                initial_line,
                f'Variable "{key}" has been already declared'
            )

        # Store as variable
        self.variables[key] = match_result.value
        return MatchResult(MatchResultType.VARIABLE)

    def list(self) -> MatchResult:
        """
        Matches with a list
        :return: Matched list
        """
        result = []

        self.maybe_match('ws')
        self.keyword('[')
        while True:
            # Discards useless lines between elements of array
            useless_line = self.maybe_match('useless_line')
            if useless_line is not None:
                continue

            item = self.maybe_match('any_type')
            if item is None:
                break

            if item.result_type == MatchResultType.EXPRESSION:
                item = item.value[0]
            else:
                item = item.value

            result.append(item)

            self.maybe_match('ws')
            self.maybe_match('new_line')
            if not self.maybe_keyword(','):
                break

        self.maybe_match('ws')
        self.maybe_match('new_line')
        self.keyword(']')
        return MatchResult(MatchResultType.LIST, result)

    def useless_line(self) -> MatchResult:
        """
        Matches with a useless line. A line is useless when it contains only whitespaces and/or a comment
        finishing in a new line
        :raise: ParseError if the line contains valid data
        :return: MatchResult indicating the presence of a useless line
        """
        self.match('ws')
        comment = self.maybe_match('comment')
        initial_line = self.line
        self.maybe_match('new_line')
        is_new_line = (self.line - initial_line) == 1

        if comment is None and not is_new_line:
            raise ParseError(
                self.pos + 1,
                self.line,
                'It is a valid line'
            )

        return MatchResult(MatchResultType.USELESS_LINE)

    def expression(self) -> MatchResult:
        """
        Match any Gura expression
        :raise: DuplicatedKeyError if any of the defined key was declared more than once
        :return: Dict with Gura string data
        """
        result = {}
        indentation_level = 0
        while self.pos < self.len:
            initial_pos = self.pos
            initial_line = self.line

            item: MatchResult = self.match('variable', 'pair', 'useless_line')

            if item is None:
                break

            if item.result_type == MatchResultType.PAIR:
                # It is a key/value pair
                key, value, indentation = item.value
                if key in result:
                    raise DuplicatedKeyError(
                        initial_pos + 1 + indentation,
                        initial_line,
                        f'The key "{key}" has been already defined'
                    )

                result[key] = value
                indentation_level = indentation

            initial_pos = self.pos
            self.maybe_match('ws')
            if self.maybe_keyword(']', ',') is not None:
                # Breaks if it is the end of a list
                self.__remove_last_indentation_level()
                self.pos -= 1
                break
            else:
                self.pos = initial_pos

        return MatchResult(MatchResultType.EXPRESSION, (result, indentation_level)) if len(result) > 0 else None

    def __remove_last_indentation_level(self):
        """Removes, if exists, the last indentation level"""
        if len(self.indentation_levels) > 0:
            self.indentation_levels.pop()

    def key(self) -> str:
        """
        Matches with a key. A key is an unquoted string followed by a colon (:)
        :raise: ParseError if key is not a valid string
        :return: Matched key
        """
        key = self.match('unquoted_string')

        if type(key) is not str:
            error_pos = self.pos + 1
            raise ParseError(
                error_pos,
                self.line,
                'Expected string for key but got "%s"',
                self.text[error_pos]
            )

        self.keyword(':')
        return key

    def pair(self) -> Optional[MatchResult]:
        """
        Matches with a key-value pair taking into consideration the indentation levels
        :return: Matched key-value pair. None if the indentation level is lower than the last one (to indicate the
        ending of a parent object)
        """
        pos_before_pair = self.pos  # To report correct position in case of exception
        current_indentation_level = self.maybe_match('ws_with_indentation')

        key = self.match('key')
        self.maybe_match('ws')

        # Check indentation
        last_indentation_block = self.__get_last_indentation_level()

        # Check if indentation is divisible by 4
        if current_indentation_level % 4 != 0:
            raise InvalidIndentationError(
                pos_before_pair,
                self.line,
                f'Indentation block ({current_indentation_level}) must be divisible by 4'
            )

        if last_indentation_block is None or current_indentation_level > last_indentation_block:
            self.indentation_levels.append(current_indentation_level)
        elif current_indentation_level < last_indentation_block:
            self.__remove_last_indentation_level()

            # As the indentation was consumed, it is needed to return to line beginning to get the indentation level
            # again in the previous matching. Otherwise, the other match would get indentation level = 0
            self.pos = pos_before_pair
            return None  # This breaks the parent loop

        # To report well the line number in case of exceptions
        initial_pos = self.pos
        initial_line = self.line

        # If it is None then is an empty expression, and therefore invalid
        result = self.match('any_type')
        if result is None:
            raise ParseError(
                self.pos + 1,
                self.line,
                'Invalid pair'
            )

        # Checks indentation against parent level
        if result.result_type == MatchResultType.EXPRESSION:
            dict_values, child_indentation_level = result.value
            if child_indentation_level == current_indentation_level:
                # Considers the error position and line for the first child
                exception_line, exception_pos = self.__exception_data_with_initial_data(child_indentation_level,
                                                                                        initial_line, initial_pos)
                child_key = list(dict_values.keys())[0]
                raise InvalidIndentationError(
                    exception_pos,
                    exception_line,
                    f'Wrong indentation level for pair with key "{child_key}" '
                    f'(parent "{key}" has the same indentation level)'
                )
            elif abs(current_indentation_level - child_indentation_level) != 4:
                exception_line, exception_pos = self.__exception_data_with_initial_data(child_indentation_level,
                                                                                        initial_line, initial_pos)
                raise InvalidIndentationError(
                    exception_pos,
                    exception_line,
                    'Difference between different indentation levels must be 4'
                )

            result = dict_values
        else:
            result = result.value

        # Prevents issues with indentation inside a list that break objects
        if isinstance(result, list):
            self.__remove_last_indentation_level()
            self.indentation_levels.append(current_indentation_level)

        self.maybe_match('new_line')

        return MatchResult(MatchResultType.PAIR, (key, result, current_indentation_level))

    @staticmethod
    def __exception_data_with_initial_data(
            child_indentation_level: int,
            initial_line: int,
            initial_pos: int
    ) -> Tuple[int, int]:
        """
        Gets the Exception position and line considering indentation. Useful for InvalidIndentationError exceptions
        :param child_indentation_level: Child pair indentation level
        :param initial_line: Initial line
        :param initial_pos: Initial position
        :return: A tuple with correct position and line
        """
        exception_pos = initial_pos + 2 + child_indentation_level
        exception_line = initial_line + 1
        return exception_line, exception_pos

    def __get_last_indentation_level(self) -> Optional[int]:
        """
        Gets the last indentation level or None in case it does not exist
        :return: Last indentation level or None if it does not exist
        """
        return None if len(self.indentation_levels) == 0 \
            else self.indentation_levels[-1]

    def null(self) -> MatchResult:
        """
        Consumes 'null' keyword and returns None
        :return None
        """
        self.keyword('null')
        return MatchResult(MatchResultType.PRIMITIVE, None)

    def empty_object(self) -> MatchResult:
        """
        Consumes 'empty' keyword and returns an empty object
        :return Empty dict (which represents an object)
        """
        self.keyword('empty')
        return MatchResult(MatchResultType.PRIMITIVE, {})

    def boolean(self) -> MatchResult:
        """
        Parses boolean values
        :return: Matched boolean value
        """
        value = self.keyword('true', 'false') == 'true'
        return MatchResult(MatchResultType.PRIMITIVE, value)

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

        return ''.join(chars).rstrip(' \t')

    def number(self) -> MatchResult:
        """
        Parses a string checking if it is a number and get its correct value
        :raise: ParseError if the extracted string is not a valid number
        :return: Returns an int or a float depending of type inference
        """
        number_type = int

        chars = [self.char(ACCEPTABLE_NUMBER_CHARS)]

        while True:
            char = self.maybe_char(ACCEPTABLE_NUMBER_CHARS)
            if char is None:
                break

            if char in 'Ee.':
                number_type = float

            chars.append(char)

        result = ''.join(chars).rstrip(' \t')

        # Checks hexadecimal and octal format
        prefix = result[:2]
        if prefix in ['0x', '0o', '0b']:
            without_prefix = result[2:]
            if prefix == '0x':
                base = 16
            elif prefix == '0o':
                base = 8
            else:
                base = 2
            return MatchResult(MatchResultType.PRIMITIVE, int(without_prefix, base))

        # Checks inf or NaN
        last_three_chars = result[-3:]
        if last_three_chars in ['inf', 'nan']:
            return MatchResult(MatchResultType.PRIMITIVE, float(result))

        try:
            return MatchResult(MatchResultType.PRIMITIVE, number_type(result))
        except ValueError:
            raise ParseError(
                self.pos + 1,
                self.line,
                f'"{result}" is not a valid number',
            )

    def basic_string(self) -> MatchResult:
        """
        Matches with a simple/multiline basic string
        :return: Matched string
        """
        quote = self.keyword('"""', '"')

        is_multiline = quote == '"""'

        # NOTE: a newline immediately following the opening delimiter will be trimmed. All other whitespace and
        # newline characters remain intact.
        if is_multiline:
            if self.maybe_char('\n') is not None:
                self.line += 1

        chars = []

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
                # Gets escaped char or interprets as literal
                else:
                    chars.append(ESCAPE_SEQUENCES.get(escape, char + escape))
            # Computes variables values in string
            elif char == '$':
                initial_pos = self.pos
                initial_line = self.line
                var_name = self.__get_var_name()
                chars.append(self.__get_variable_value(var_name, initial_pos, initial_line))
            else:
                chars.append(char)

        return MatchResult(MatchResultType.PRIMITIVE, ''.join(chars))

    def literal_string(self) -> MatchResult:
        """
        Matches with a simple/multiline literal string
        :return: Matched string
        """
        quote = self.keyword("'''", "'")

        is_multiline = quote == "'''"

        # NOTE: a newline immediately following the opening delimiter will be trimmed. All other whitespace and
        # newline characters remain intact.
        if is_multiline:
            if self.maybe_char('\n') is not None:
                self.line += 1

        chars = []

        while True:
            closing_quote = self.maybe_keyword(quote)
            if closing_quote is not None:
                break

            char = self.char()
            chars.append(char)

        return MatchResult(MatchResultType.PRIMITIVE, ''.join(chars))

    def dumps(self, value: Dict) -> str:
        """
        Generates a Gura string from a dictionary (aka. stringify). Takes a value, check its type and returns its
        correct value in a recursive way
        :param value: Value retrieved from dict to transform in string
        an object or array
        :return: String representation of the received value
        """
        if value is None:
            return 'null'

        value_type = type(value)
        if value_type == str:
            result = ''

            # Escapes everything that needs to be escaped
            for char in value:
                result += SEQUENCES_TO_ESCAPE.get(char, char)

            return f'"{result}"'
        if value_type == bool:
            return 'true' if value is True else 'false'
        if value_type in (int, float):
            return str(value)
        if value_type == dict:
            if len(value) == 0:
                return 'empty'
            result = ''
            for key, dict_value in value.items():
                result += f'{key}:'

                # If the value is an object, splits the stringified value by
                # newline and indents each line before adding it to the result
                if type(dict_value) == dict:
                    stringified_value = self.dumps(dict_value).rstrip()
                    if len(dict_value) > 0:
                        result += '\n'

                        for line in stringified_value.split('\n'):
                            result += INDENT + line + '\n'
                    else:
                        # Prevents indentation on empty objects
                        result += ' ' + stringified_value + '\n'
                # Otherwise adds the stringified value
                else:
                    result += f' {self.dumps(dict_value)}\n'

            return result
        if value_type == list:
            should_multiline = any((type(e) == dict or type(e) == list) and len(e) > 0 for e in value)

            if not should_multiline:
                stringify_values = list(map(self.dumps, value))
                return f'[{", ".join(stringify_values)}]'

            result = '['

            last_idx = len(value) - 1
            for idx, entry in enumerate(value):
                stringified_value = self.dumps(entry).rstrip()

                result += '\n'

                # If the stringified value contains multiple lines, indents all
                # of them and adds them all to the result
                if '\n' in stringified_value:
                    splitted = stringified_value.split('\n')
                    splitted = map(lambda element: INDENT + element, splitted)
                    result += '\n'.join(splitted)
                else:
                    # Otherwise indent the value and add to result
                    result += INDENT + stringified_value

                # Add a comma if this entry is not the final entry in the list
                if idx < last_idx:
                    result += ','

            result += '\n]'
            return result

        raise TypeError()


def loads(text: str) -> Dict:
    """
    Parses a text in Gura format
    :param text: Text to be parsed
    :raise: ParseError if the syntax of text is invalid
    :return: Dict with all the parsed values
    """
    return GuraParser().loads(text)


def dumps(data: Dict) -> str:
    """
    Generates a Gura string from a dictionary (aka. Stringify)
    :param data: Dictionary data to stringify
    :return: String with the data in Gura format
    """
    # content = GuraParser().dumps(data, indentation_level=0, new_line=True)
    content = GuraParser().dumps(data)
    return content.lstrip('\n').rstrip('\n')
