from typing import Dict, Any, Union
from parser import ParseError, Parser


class GuraParser(Parser):
    variables: Dict[str, Any]

    def __init__(self):
        super(GuraParser, self).__init__()
        self.variables = {}

    def eat_whitespace(self):
        """Removes white spaces and comments which start with '#'"""
        is_processing_comment = False

        while self.pos < self.len:
            char = self.text[self.pos + 1]
            if is_processing_comment:
                if char == '\n':
                    is_processing_comment = False
            else:
                if char == '#':
                    is_processing_comment = True
                elif char not in ' \f\v\r\t\n':
                    break

            self.pos += 1

    def start(self):
        return self.match('map')

    # def expression(self):
        # return self.match('variable', 'complex_type', 'primitive_type')
        # return self.match('complex_type', 'primitive_type')
        # return self.match('complex_type')

    def any_type(self):
        return self.match('primitive_type', 'complex_type')

    def primitive_type(self):
        return self.match('null', 'boolean', 'quoted_string', 'string_or_number')

    def complex_type(self):
        # return self.match('variable', 'list', 'map')
        # return self.match('map')
        return self.match('list', 'map')

    def variable(self):
        """TODO: use"""
        error_message = None

        self.keyword('$')
        key, value = self.match('pair')

        if key in self.variables:
            error_message = f'Variable \'{key}\' has been already declared'

        if error_message is not None:
            raise ParseError(
                self.pos + 1,
                error_message,
                self.text[self.pos + 1]
            )

        # Store as variable
        self.variables[key] = value
        return None

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

    def map(self):
        rv = {}

        while True:
            item = self.maybe_match('pair')
            if item is None:
                break

            key, value = item
            if key in rv:
                raise ParseError(
                    self.pos + 1,
                    f'The key \'{key}\' has been already defined',
                )
            rv[key] = value

        return rv

    def pair(self):
        key = self.match('unquoted_string')
        if type(key) is not str:
            raise ParseError(
                self.pos + 1,
                'Expected string but got number',
                self.text[self.pos + 1]
            )

        self.keyword(':')
        value = self.match('any_type')

        return key, value

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
        acceptable_chars = '0-9A-Za-z \t!$%&()*+./;<=>?^_`|~-'
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
        with open('tests/prueba.gura', 'r') as file:
            pprint(parser.parse(file.read()))
    except ParseError as e:
        print('Error: ', str(e))
