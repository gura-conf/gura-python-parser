from typing import Optional, Any


class ParseError(Exception):
    def __init__(self, pos: int, line: int, msg: str, *args):
        self.pos = pos
        self.line = line
        self.msg = msg
        self.args = args

    def __str__(self):
        return '%s at line %s position %s' % (self.msg % self.args, self.line, self.pos)


class Parser:
    """Base parser"""
    text: str
    pos: int
    line: int
    len: int

    def __init__(self):
        self.cache = {}

    def assert_end(self):
        """
        Checks that the parser has reached the end of file, otherwise it will raise a ParseError
        :raise: ParseError if EOL has not been reached
        """
        if self.pos < self.len:
            raise ParseError(
                self.pos + 1,
                self.line,
                'Expected end of string but got %s',
                self.text[self.pos + 1]
            )

    def split_char_ranges(self, chars: str):
        """
        Generates a list of char from a list of char which could container char ranges (i.e. a-z or 0-9)
        :param chars: List of chars to process
        :return: List of char with ranges processed
        """
        try:
            return self.cache[chars]
        except KeyError:
            pass

        result = []
        index = 0
        length = len(chars)

        while index < length:
            if index + 2 < length and chars[index + 1] == '-':
                if chars[index] >= chars[index + 2]:
                    raise ValueError('Bad character range')

                result.append(chars[index:index + 3])
                index += 3
            else:
                result.append(chars[index])
                index += 1

        self.cache[chars] = result
        return result

    def char(self, chars: Optional[str] = None) -> str:
        """
        Matches a list of specific chars and returns the first that matched. If any matched, it will raise a ParseError
        :param chars: Chars to match. If it is None, it will return the next char in text
        :raise: ParseError if any of the specified char (i.e. if chars != None) matched
        :return: Matched char
        """
        if self.pos >= self.len:
            raise ParseError(
                self.pos + 1,
                self.line,
                'Expected %s but got end of string',
                'character' if chars is None else '[%s]' % chars
            )

        next_char = self.text[self.pos + 1]
        if chars is None:
            self.pos += 1
            return next_char

        for char_range in self.split_char_ranges(chars):
            if len(char_range) == 1:
                if next_char == char_range:
                    self.pos += 1
                    return next_char
            elif char_range[0] <= next_char <= char_range[2]:
                self.pos += 1
                return next_char

        raise ParseError(
            self.pos + 1,
            self.line,
            'Expected [%s] but got %s' % (chars, next_char)
        )

    def keyword(self, *keywords: str):
        """
        Matches specific keywords
        :param keywords: Keywords to match
        :raise: ParseError if any of the specified keywords matched
        :return: The first matched keyword
        """
        if self.pos >= self.len:
            raise ParseError(
                self.pos + 1,
                self.line,
                'Expected %s but got end of string',
                ','.join(keywords)
            )

        for keyword in keywords:
            low = self.pos + 1
            high = low + len(keyword)

            if self.text[low:high] == keyword:
                self.pos += len(keyword)
                return keyword

        raise ParseError(
            self.pos + 1,
            self.line,
            'Expected %s but got %s',
            ','.join(keywords),
            self.text[self.pos + 1],
        )

    def match(self, *rules: str):
        """
        Matches specific rules which name must be implemented as a method in corresponding parser. A rule does not match
        if its method raises ParseError
        :param rules: Rules to match
        :raise: ParseError if any of the specified rules matched
        :return: The first matched rule method's result
        """
        last_error_pos = -1
        last_exception = None
        last_error_rules = []

        for rule in rules:
            initial_pos = self.pos
            try:
                result = getattr(self, rule)()
                return result
            except ParseError as e:
                self.pos = initial_pos

                if e.pos > last_error_pos:
                    last_exception = e
                    last_error_pos = e.pos
                    last_error_rules.clear()
                    last_error_rules.append(rule)
                elif e.pos == last_error_pos:
                    last_error_rules.append(rule)

        if len(last_error_rules) == 1:
            raise last_exception
        else:
            last_error_pos = min(len(self.text) - 1, last_error_pos)
            raise ParseError(
                last_error_pos,
                self.line,
                'Expected %s but got %s',
                ','.join(last_error_rules),
                self.text[last_error_pos]
            )

    def maybe_char(self, chars: Optional[str] = None) -> Optional[str]:
        """
        Like char() but returns None instead of raising ParseError
        :param chars: Chars to match. If it is None, it will return the next char in text
        :return: Char if matched, None otherwise
        """
        try:
            return self.char(chars)
        except ParseError:
            return None

    def maybe_match(self, *rules: str) -> Optional[Any]:
        """
        Like match() but returns None instead of raising ParseError
        :param rules: Rules to match
        :return: Rule result if matched, None otherwise
        """
        try:
            return self.match(*rules)
        except ParseError:
            return None

    def maybe_keyword(self, *keywords: str) -> Optional[str]:
        """
        Like keyword() but returns None instead of raising ParseError
        :param keywords: Keywords to match
        :return: Keyword if matched, None otherwise
        """
        try:
            return self.keyword(*keywords)
        except ParseError:
            return None
