import io

from typing import Iterable, IO

from . import tokens
from .tokens import NumberToken, Token, TokenType

EOF = 'EOF'


class ZincTokenizerException(Exception):
    """An exception indicating that the string could not be tokenized."""
    pass


def _is_letter(c: str) -> bool:
    return c != EOF and (('a' <= c and c <= 'z') or ('A' <= c and c <= 'Z'))


def _is_digit(c: str) -> bool:
    return '0' <= c <= '9'


def _is_id_start(c: str) -> bool:
    return c != EOF and 'a' <= c and c <= 'z'


def _is_id_part(c: str) -> bool:
    return _is_letter(c) or _is_digit(c) or c == '_'


def tokenize(s: str) -> Iterable[Token]:
    """Tokenize a Zinc string."""
    return tokenize_buf(io.StringIO(s))


def tokenize_buf(buf: IO) -> Iterable[Token]:
    """Tokenize a Zinc buffer."""
    tkzr = ZincTokenizer(buf)
    while True:
        tok = next(tkzr)
        yield tok
        if tok is tokens.EOF:
            break


class ZincTokenizer:
    """Tokenizer for the Zinc format.

    Adapted from the Java reference implementation by Brian Frank.

    FMI: https://project-haystack.org/doc/Zinc
    """

    def __init__(self, buf: IO):
        self._buf = buf  # type: IO
        self._cur = None  # type: str
        self._peek = None  # type: str
        self.line = 0  # type: int
        self._consume()
        self._consume()

    def __next__(self) -> Token:
        # skip non-meaningful whitespace
        while True:
            if self._cur in (' ', '\t', '\xa0'):
                self._consume()
                continue
            # TODO: skip comments?
            break

        if self._cur in ('\n', '\r'):
            if self._cur == '\r' and self._peek == '\n':
                self._consume('\r')
            self._consume()
            self.line += 1
            return tokens.NEWLINE

        # handle various starting chars
        if self._cur == EOF:
            return tokens.EOF
        if _is_id_start(self._cur):
            return self._tokenize_id()
        if self._cur == 'C' and self._peek == '(':
            return self._tokenize_coord()
        if self._cur.isupper():
            return self._tokenize_reserved()
        if self._cur == '"':
            return self._tokenize_str()
        if self._cur == '@':
            return self._tokenize_ref()
        if self._cur == '`':
            return self._tokenize_uri()
        if (_is_digit(self._cur) or
           (self._cur == '-' and _is_digit(self._peek))):
            return self._tokenize_num()
        # otherwise, symbol
        return self._tokenize_symbol()

    def _tokenize_id(self):
        s = []
        while self._cur != EOF and _is_id_part(self._cur):
            s.append(self._cur)
            self._consume()
        return Token(TokenType.ID, ''.join(s))

    def _tokenize_coord(self):
        s = ['C', '(']
        self._consume('C')
        self._consume('(')
        # lat
        s.append(self._consume_decimal_unscientific())
        s.append(',')
        self._consume(',')
        # allow one optional space
        if self._cur == ' ':
            self._consume()
        # lng
        s.append(self._consume_decimal_unscientific())
        s.append(')')
        self._consume(')')
        return Token(TokenType.COORD, ''.join(s))

    def _consume_decimal_unscientific(self) -> str:
        s = []
        if self._cur == '-':
            s.append(self._cur)
            self._consume()
        dots = 0
        while _is_digit(self._cur) or self._cur == '.':
            if self._cur == '.':
                dots += 1
            s.append(self._cur)
            self._consume()
        v = ''.join(s)
        if dots > 1:
            raise ZincTokenizerException(f"Invalid float {v}")
        return v

    def _tokenize_reserved(self):
        s = []
        while self._cur != EOF and _is_letter(self._cur):
            s.append(self._cur)
            self._consume()
        v = ''.join(s)
        if v == 'N':
            return tokens.NULL
        if v == 'M':
            return tokens.MARKER
        if v == 'R':
            return tokens.REMOVE
        if v == 'NA':
            return tokens.NA
        if v == 'NaN':
            return tokens.NAN
        if v == 'T':
            return tokens.TRUE
        if v == 'F':
            return tokens.FALSE
        if v == 'INF':
            return tokens.POS_INF

        raise ZincTokenizerException(f"Invalid token {v}")

    def _tokenize_num(self):
        def _is_unit(c: str):
            return c != EOF and (c in ('%', '$', '/') or ord(c) > 128)
        if self._cur == '0' and self._peek == 'x':
            self._tokenize_hex()

        # consume all things that might be part of this number token
        s = []
        colons = 0
        dashes = 0
        unit_index = 0
        exp = False
        while True:
            if self._cur is EOF:
                break
            if not _is_digit(self._cur):
                if exp and (self._cur in ('+', '-')):
                    # this is exponent notation
                    pass
                elif self._cur == '-':
                    dashes += 1
                elif self._cur == ':' and _is_digit(self._peek):
                    colons += 1
                elif ((exp or colons >= 1) and self._cur == '+'):
                    pass
                elif self._cur == '.':
                    if not _is_digit(self._peek):
                        break
                elif (self._cur in ('e', 'E') and
                      (self._peek in ('-', '+') or _is_digit(self._peek))):
                    exp = True

                elif _is_letter(self._cur) or _is_unit(self._cur):
                    if unit_index == 0:
                        unit_index = len(s)
                elif self._cur == '_':
                    if unit_index == 0 and _is_digit(self._peek):
                        self._consume()
                        continue
                    elif unit_index == 0:
                        unit_index = len(s)
                else:
                    # done with the number
                    break

            s.append(self._cur)
            self._consume()

        if dashes == 2 and colons == 0:
            return Token(TokenType.DATE, ''.join(s))
        if dashes == 0 and colons >= 1:
            return self._tokenize_time(''.join(s), 1)
        if dashes >= 2:
            return self._tokenize_datetime(''.join(s))

        return NumberToken(''.join(s), unit_index)

    def _tokenize_hex(self):
        self._consume('0')
        self._consume('x')
        s = []
        while True:
            if self._cur in '0123456789abcdefABCDEF':
                s.append(self._cur)
                self._consume()
                continue
            if self._cur == '_':
                continue
            break
        return Token(TokenType.HEX, ''.join(s), base=16)

    def _tokenize_time(self, s: str, colons: int) -> Token:
        if s and s[1] == ':':
            s = '0' + s
        if self._peek is not EOF and self._peek.isupper():
            tz = self._consume_timezone()
            return Token(TokenType.TIME, s + tz)

    def _tokenize_datetime(self, s: str) -> Token:
        if self._peek is not EOF and self._peek.isupper():
            tz = self._consume_timezone()
            return Token(TokenType.DATETIME, s + tz)
        return Token(TokenType.DATETIME, s)

    def _consume_timezone(self) -> str:
        tz = []
        if self._cur != ' ' or not self._peek.isupper():
            raise ZincTokenizerException("Expecting timezone!")
        self._consume()
        tz.append(' ')
        while _is_id_part(self._cur):
            tz.append(self._cur)
            self._consume()

            if self._cur in '+-' and ''.join(tz).endswith('GMT'):
                tz.append(self._cur)
                self._consume()
                while _is_digit(self._cur):
                    tz.append(self._cur)
                    self._consume()
        return ''.join(tz)

    def _tokenize_str(self):
        self._consume('"')
        s = []
        while True:
            if self._cur == EOF:
                raise ZincTokenizerException("Unexpected end of str")
            if self._cur == '"':
                self._consume('"')
                break
            if self._cur == '\\':
                s.append(self._escape())
                continue
            s.append(self._cur)
            self._consume()
        return Token(TokenType.STRING, ''.join(s))

    def _tokenize_ref(self):
        def _is_ref_char(c: str) -> bool:
            return _is_letter(c) or _is_digit(c) or c in '_:-.~'
        self._consume('@')
        s = []
        while True:
            if _is_ref_char(self._cur):
                s.append(self._cur)
                self._consume()
            elif self._cur == ' ' and self._peek == '"':
                # upcoming quote is the display name for the ref
                s.append(self._cur)
                self._consume()
                s += '"' + self._tokenize_str().val + '"'
            else:
                break
        return Token(TokenType.REF, ''.join(s))

    def _tokenize_uri(self):
        self._consume('`')
        s = []
        while True:
            if self._cur == '`':
                self._consume('`')
                break
            if self._cur == EOF or self._cur == '\n':
                raise ZincTokenizerException("Unexpected end of URI")
            if self._cur == '\\':
                if self._peek in ':/?#[]@\\&=;':
                    s.append(self._cur)
                    s._consume()
                    s.append(self._cur)
                    s._consume()
                else:
                    s.append(self._escape())
            else:
                s.append(self._cur)
                self._consume()
        return Token(TokenType.URI, ''.join(s))

    def _escape(self):
        self._consume('\\')
        if self._cur in 'bfnrt"$\'`\\':
            s = '\\' + self._cur
            self._consume()
            return s
        # check for uxxxx
        if self._cur == 'u':
            s = []
            self._consume('u')
            for _ in range(4):
                s.append(self._cur)
                self._consume()
            s = ''.join(s)
            try:
                return chr(int(s, base=16))
            except ValueError:
                raise ZincTokenizerException(
                    f"Invalid unicode sequence: {s}")
        raise ZincTokenizerException(f"Invalid escape sequence: {self._cur}")

    def _tokenize_symbol(self):
        c = self._cur
        self._consume()
        if c == ',':
            return tokens.COMMA
        elif c == ':':
            return tokens.COLON
        elif c == ';':
            return tokens.SEMICOLON
        elif c == '[':
            return tokens.LBRACKET
        elif c == ']':
            return tokens.RBRACKET
        elif c == '{':
            return tokens.LBRACE
        elif c == '}':
            return tokens.RBRACE
        elif c == '(':
            return tokens.LPAREN
        elif c == ')':
            return tokens.RPAREN
        elif c == '<':
            if self._cur == '<':
                self.consume('<')
                return tokens.DOUBLELT
            if self._cur == '=':
                self.consume('=')
                return tokens.LTEQ
            return tokens.LT
        elif c == '>':
            if self._cur == '>':
                self.consume('>')
                return tokens.DOUBLEGT
            if self._cur == '=':
                self.consume('=')
                return tokens.GTEQ
            return tokens.GT
        elif c == '-':
            if self._cur == '>':
                self._consume('>')
                return tokens.ARROW
            return tokens.MINUS
        elif c == '=':
            if self._cur == '=':
                self._consume('=')
                return tokens.EQUALS
            return tokens.ASSIGN
        elif c == '!':
            if self._cur == '=':
                self._consume('=')
                return tokens.NOTEQUALS
            return tokens.BANG
        elif c == '/':
            return tokens.SLASH
        raise ZincTokenizerException(f"Unexpected symbol: '{c}'")

    def _consume(self, expected=None):
        if expected is not None and self._cur != expected:
            raise ZincTokenizerException(
                f"Expected {expected} but found {self._cur}")
        try:
            self._cur = self._peek
            self._peek = self._buf.read(1) or EOF
        except Exception:
            self._cur = EOF
            self._peek = EOF
