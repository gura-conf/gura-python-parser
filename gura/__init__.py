from gura.GuraParser import GuraParser, InvalidIndentationError, DuplicatedVariableError, DuplicatedKeyError, \
    VariableNotDefinedError, DuplicatedImportError, loads, dumps
from gura.Parser import ParseError

__version__ = "1.2.0"

loads = loads
dumps = dumps
ParseError = ParseError
InvalidIndentationError = InvalidIndentationError
DuplicatedVariableError = DuplicatedVariableError
DuplicatedKeyError = DuplicatedKeyError
VariableNotDefinedError = VariableNotDefinedError
DuplicatedImportError = DuplicatedImportError
