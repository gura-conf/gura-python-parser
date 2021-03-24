from typing import Dict, Any, Union, Optional, List
from parser import ParseError, Parser
from enum import Enum, auto


class MatchResultType(Enum):
    USELESS_LINE = auto(),
    PAIR = auto()


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
        print(f'devolviendo -> {current_indentation_level}')
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
        raise ParseError(
            self.pos + 1,
            self.line,
            f'Wrong indentation character! Using {good_char} but received {received_char}',
            self.text[self.pos + 1]
        )

    def start(self):
        rv = self.match('map')
        self.eat_ws_and_new_lines()
        return rv

    def any_type(self):
        return self.match('primitive_type', 'complex_type')

    def primitive_type(self):
        return self.match('null', 'boolean', 'quoted_string', 'string_or_number')

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

        self.keyword('[')
        while True:
            item = self.maybe_match('any_type')
            if item is None:
                break

            rv.append(item)

            if not self.maybe_keyword(','):
                break

        self.keyword(']')
        return rv

    def useless_line(self):
        self.match('ws')
        self.maybe_match('comment')
        self.maybe_match('new_line')
        return MatchResult(MatchResultType.USELESS_LINE)

    def map(self):
        rv = {}
        while self.pos < self.len:
            # self.maybe_match('useless_line')
            current_indentation_level = self.maybe_match('ws_with_indentation')

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
                self.indentation_levels.pop()

                # As the indentation was consumed, it is needed to return to line beginning to get the indentation level
                # again in the previous matching. Otherwise, the other match would get indentation level = 0
                self.pos -= current_indentation_level
                break

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

        return rv

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
        key = self.match('key')
        self.maybe_match('ws')
        self.maybe_match('new_line')
        value = self.match('any_type')
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
        acceptable_chars = '0-9A-Za-z \t!$%&()*+./;<=>?^_`|~-'

        chars = [self.char(acceptable_chars)]

        while True:
            char = self.maybe_char(acceptable_chars)
            if char is None:
                break

            chars.append(char)

        return ''.join(chars).rstrip(' \t')

    def string_or_number(self) -> Union[float, int, str]:
        """
        Parses a string checking if it is a number.
        :return: Returns an int, a float or a string depending of type inference
        """
        acceptable_chars = '0-9A-Za-z!$%&()*+./;<=>?^_`|~-'
        number_type = int

        chars = [self.char(acceptable_chars)]

        while True:
            char = self.maybe_char(acceptable_chars)
            if char is None:
                break

            if char in 'Ee.':
                number_type = float

            chars.append(char)

        rv = ''.join(chars).rstrip(' \t')
        try:
            return number_type(rv)
        except ValueError:
            return rv

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
