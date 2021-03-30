from typing import Dict, Any, Union, Optional, List
from parser import ParseError, Parser
from enum import Enum, auto

# Number chars
BASIC_NUMBERS_CHARS = '0-9'
HEX_OCT_BIN = 'A-Fa-fxob'
INF_AND_NAN = 'in'  # The rest of the chars are defined in hex_oct_bin
# IMPORTANT: '-' char must be last, otherwise it will be interpreted as a range
ACCEPTABLE_NUMBER_CHARS = BASIC_NUMBERS_CHARS + HEX_OCT_BIN + INF_AND_NAN + 'Ee+._-'


class MatchResultType(Enum):
    USELESS_LINE = auto(),
    PAIR = auto()
    COMMENT = auto()


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

    def __init__(self):
        super(GuraParser, self).__init__()
        self.variables = {}
        self.indent_char = None
        self.indentation_levels = []

    def new_line(self):
        res = self.char('\f\v\r\n')
        if res is not None:
            self.line += 1

    def comment(self):
        self.keyword('#')
        while self.pos < self.len:
            char = self.text[self.pos + 1]
            # char = self.text[self.pos]
            self.pos += 1
            if char in '\f\v\r\n':
                self.line += 1
                break
        print(f'Puntero en -> {self.text[self.pos]} (pos -> {self.pos})')
        return MatchResult(MatchResultType.COMMENT)

    def ws_with_indentation(self):
        """
        Removes white spaces and comments which start with '#'
        TODO: complete
        :param check_indentation:
        :return:
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
        Removes white spaces and comments which start with '#'
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

    def start(self):
        rv = self.match('map')
        self.eat_ws_and_new_lines()
        return rv

    def any_type(self):
        rv = self.maybe_match('primitive_type')
        if rv is not None:
            return rv

        # Checks if user defined an unquoted value
        # TODO: uncomment when all tests pass
        # unquoted = self.maybe_match('unquoted_string')
        # colon = self.maybe_keyword(':')
        # if unquoted and colon is None:
        # if unquoted:
        #     raise ValueError(f'String value \'{unquoted}\' is not valid as unquoted strings are not allowed')
        # elif colon is not None:
        #     self.pos -= len(unquoted) + 1  # Considers colon length too

        return self.match('complex_type')

    def primitive_type(self):
        self.maybe_match('ws')
        return self.match('null', 'boolean', 'quoted_string', 'number')

    def complex_type(self):
        # return self.match('variable', 'list', 'map')
        # return self.match('map')
        return self.match('list', 'map')

    # def variable(self):
    #     """TODO: use"""
    #     error_message = None
    #
    #     self.keyword('$')
    #     key, value = self.match('pair')
    #
    #     if key in self.variables:
    #         error_message = f'Variable \'{key}\' has been already declared'
    #
    #     if error_message is not None:
    #         raise ParseError(
    #             self.pos + 1,
    #             self.line,
    #             error_message,
    #             self.text[self.pos + 1]
    #         )
    #
    #     # Store as variable
    #     self.variables[key] = value
    #     return None

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
            # item: MatchResult = self.maybe_match('pair')  # TODO: if tests pass, check this one
            item: MatchResult = self.maybe_match('pair', 'useless_line')

            if item is None:
                break

            if item.result_type == MatchResultType.PAIR:
                # It is a key/value pair
                key, value = item.value
                print(f"Pair obtenido '{item.value}'")
                if key in rv:
                    raise ParseError(
                        self.pos + 1,
                        self.line,
                        f'The key \'{key}\' has been already defined',
                    )

                rv[key] = value

            if self.maybe_keyword(']', ',') is not None:
                print('"]" o "," matchearon')
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
        acceptable_chars = '0-9A-Za-z!$%&()*+./;<=>?^_`|~-'

        chars = [self.char(acceptable_chars)]

        while True:
            char = self.maybe_char(acceptable_chars)
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

    def quoted_string(self):
        quote = self.char('"\'')
        chars = []

        escape_sequences = {
            'b': '\b',
            'f': '\f',
            'n': '\n',
            'r': '\r',
            't': '\t',
        }

        while True:
            char = self.char()
            if char == quote:
                break
            elif char == '\\':
                escape = self.char()
                if escape == 'u':
                    code_point = []
                    for i in range(4):
                        code_point.append(self.char('0-9a-fA-F'))

                    chars.append(chr(int(''.join(code_point), 16)))
                else:
                    chars.append(escape_sequences.get(char, char))
            else:
                chars.append(char)

        return ''.join(chars)


if __name__ == '__main__':
    from pprint import pprint

    parser = GuraParser()

    try:
        # pprint(parser.parse(sys.stdin.read()))
        with open('tests/prueba.ura', 'r') as file:
            pprint(parser.parse(file.read()))
    except ParseError as e:
        print('Error: ', str(e))
