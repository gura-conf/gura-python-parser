from gura.GuraParser import GuraParser, InvalidIndentationError, DuplicatedVariableError, DuplicatedKeyError, \
    VariableNotDefinedError, DuplicatedImportError, loads, dumps
from gura.Parser import ParseError, GuraError

__version__ = "1.4.3"

loads = loads
dumps = dumps
GuraError = GuraError
ParseError = ParseError
InvalidIndentationError = InvalidIndentationError
DuplicatedVariableError = DuplicatedVariableError
DuplicatedKeyError = DuplicatedKeyError
VariableNotDefinedError = VariableNotDefinedError
DuplicatedImportError = DuplicatedImportError
