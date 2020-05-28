from enum import auto, Enum


class TokenType(Enum):
    # Primitive tokens
    EOF = auto()
    NEWLINE = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    LPAREN = auto()
    RPAREN = auto()
    LT = auto()
    LTEQ = auto()
    DOUBLELT = auto()
    GT = auto()
    GTEQ = auto()
    DOUBLEGT = auto()
    ARROW = auto()
    MINUS = auto()
    EQUALS = auto()
    NOTEQUALS = auto()
    ASSIGN = auto()
    BANG = auto()
    SLASH = auto()
    # Dynamic tokens
    ID = auto()
    RESERVED = auto()
    STRING = auto()
    REF = auto()
    DATE = auto()
    TIME = auto()
    DATETIME = auto()
    COORD = auto()
    URI = auto()
    XSTR = auto()
    NUMBER = auto()


class Token:
    def __init__(self, ttype: TokenType, val: str):
        self.ttype = ttype
        self.val = val

    def __repr__(self):
        return f"Token({self.ttype}, {self.val.__repr__()})"

    def __str__(self):
        return f"Token({self.ttype}, {self.val})"

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if other is self:
            return True
        return self.ttype == other.ttype and self.val == other.val


class NumberToken(Token):
    def __init__(self, val: str, unit_index: int):
        self.ttype = TokenType.NUMBER
        self.val = val
        self.unit_index = unit_index

    def __repr__(self):
        return (f"{self.__class__}({self.ttype.__repr__()}, "
                f"{self.val.__repr__()}, unit_index={self.unit_index}")

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if other is self:
            return True
        return (self.ttype == other.ttype and
                self.val == other.val and
                self.unit_index == other.unit_index)


EOF = Token(TokenType.EOF, 'EOF')
NEWLINE = Token(TokenType.NEWLINE, '\n')
COMMA = Token(TokenType.COMMA, ',')
COLON = Token(TokenType.COLON, ':')
SEMICOLON = Token(TokenType.SEMICOLON, ';')
LBRACKET = Token(TokenType.LBRACKET, '[')
RBRACKET = Token(TokenType.RBRACKET, ']')
LBRACE = Token(TokenType.LBRACE, '{')
RBRACE = Token(TokenType.RBRACE, '}')
LPAREN = Token(TokenType.LPAREN, '(')
RPAREN = Token(TokenType.RPAREN, ')')
LT = Token(TokenType.LT, '<')
LTEQ = Token(TokenType.LTEQ, '<=')
DOUBLELT = Token(TokenType.DOUBLELT, '<<')
GT = Token(TokenType.GT, '>')
GTEQ = Token(TokenType.GTEQ, '>=')
DOUBLEGT = Token(TokenType.DOUBLEGT, '>>')
ARROW = Token(TokenType.ARROW, '->')
MINUS = Token(TokenType.MINUS, '-')
EQUALS = Token(TokenType.EQUALS, '==')
NOTEQUALS = Token(TokenType.NOTEQUALS, '!=')
ASSIGN = Token(TokenType.ASSIGN, '=')
BANG = Token(TokenType.BANG, '!')
SLASH = Token(TokenType.SLASH, '/')

# Reserved word tokens
NULL = Token(TokenType.RESERVED, 'N')
MARKER = Token(TokenType.RESERVED, 'M')
REMOVE = Token(TokenType.RESERVED, 'R')
NA = Token(TokenType.RESERVED, 'NA')
NAN = Token(TokenType.RESERVED, 'NaN')
POS_INF = Token(TokenType.RESERVED, 'INF')
NEG_INF = Token(TokenType.RESERVED, '-INF')
TRUE = Token(TokenType.RESERVED, 'T')
FALSE = Token(TokenType.RESERVED, 'F')
