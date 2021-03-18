from parser import ParseError, Parser


class GuraParser(Parser):
    def eat_whitespace(self):
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
        return self.match('expression')

    def expression(self):
        return self.match('complex_type', 'primitive_type')

    def primitive_type(self):
        return self.match('null', 'boolean', 'quoted_string', 'unquoted')

    def complex_type(self):
        return self.match('list', 'map')

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

        self.keyword('{')
        while True:
            item = self.maybe_match('pair')
            if item is None:
                break

            rv[item[0]] = item[1]

            if not self.maybe_keyword(','):
                break

        self.keyword('}')
        return rv

    def pair(self):
        key = self.match('quoted_string', 'unquoted')

        if type(key) is not str:
            raise ParseError(
                self.pos + 1,
                'Expected string but got number',
                self.text[self.pos + 1]
            )

        self.keyword(':')
        value = self.match('any_type')

        return key, value

    def null(self):
        self.keyword('null')
        return None

    def boolean(self):
        boolean = self.keyword('true', 'false')
        return boolean[0] == 't'

    def unquoted(self):
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
    import sys
    from pprint import pprint

    parser = JSONParser()

    try:
        pprint(parser.parse(sys.stdin.read()))
    except ParseError as e:
        print('Error: '+ str(e))
