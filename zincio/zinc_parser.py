import io
from os import PathLike
import pandas as pd  # type: ignore
from typing import Dict, IO, List, Optional, Union

from .dtypes import (
    NULL,
    MARKER,
    REMOVE,
    NA,
    POS_INF,
    NAN,
    BOOL_TRUE,
    BOOL_FALSE,
    Coord,
    Datetime,
    Number,
    Ref,
    Scalar,
    String,
    Uri,
    XStr,
)
from .grid import Grid, GridBuilder
from . import tokens
from .tokens import NumberToken, Token, TokenType
from .zinc_tokenizer import ZincTokenizer

# Type alias
FilePathOrBuffer = Union[str, bytes, int, PathLike, io.StringIO]


class ZincParseException(Exception):
    pass


class ZincErrorGridException(Exception):
    pass


def parse(s: Union[bytes, str]) -> Grid:
    """Parses utf-8 encoded string to a Grid.

    Arguments:
        s: bytes or utf-8 encoded string to be parsed.
    """
    if isinstance(s, bytes):
        return read(io.StringIO(s.decode()))
    return read(io.StringIO(s))


def read(filepath_or_buffer: FilePathOrBuffer) -> Grid:
    """Reads utf-8 encoded Zinc file or buffer to a Grid.

    Arguments:
        filepath_or_buffer: str, path object, or file-like object
            Accepts any path-like object that can be opened or a file-like
            object that has a read() method.
    """
    with _handle_buf(filepath_or_buffer) as buf:
        return ZincParser(ZincTokenizer(buf)).parse()


def _handle_buf(filepath_or_buffer: FilePathOrBuffer) -> IO:
    if isinstance(filepath_or_buffer, io.StringIO):
        return filepath_or_buffer
    return open(filepath_or_buffer, encoding="utf-8")


class ZincParser:
    """ZincParser parses a Zinc-format string into a Grid."""

    def __init__(self, tokenizer: ZincTokenizer):
        self._tokenizer: ZincTokenizer = tokenizer
        self._cur: Token = tokens.EOF
        self._peek: Token = tokens.EOF
        self._cur_line: int = 0
        self._peek_line: int = 0
        self._version: int = 3
        self._consume()
        self._consume()

    def parse(self, close: Optional[bool] = True) -> Grid:
        try:
            grid = self._parse_grid()
            self._verify_eq(tokens.EOF)
            return grid
        finally:
            self._tokenizer._buf.close()

    def _parse_grid(self) -> Grid:
        def _check_version(s: String):
            if s == String('3.0'):
                return 3
            if s == String('2.0'):
                return 2
            raise ZincParseException(f"Unsupported Zinc version {s}")

        if not (self._cur.ttype is TokenType.ID and self._cur.val == 'ver'):
            raise ZincParseException(
                f"Expecting grid 'ver' identifier, but found {self._cur}")
        self._consume()
        self._consume_i(tokens.COLON)

        gb = GridBuilder(_check_version(self._consume_str()))

        # Grid meta
        if self._cur.ttype is TokenType.ID:
            grid_meta = self._parse_dict()
            # Check for errors
            if 'err' in grid_meta:
                raise ZincErrorGridException("Error grid received")
            gb.add_meta(grid_meta)
        self._consume_i(tokens.NEWLINE)

        # Column definitions
        num_cols: int = 0
        while self._cur.ttype is TokenType.ID:
            num_cols += 1
            colname: str = self._consume_tag_id()
            col_meta: Dict[str, Scalar] = {}
            if self._cur.ttype is TokenType.ID:
                col_meta = self._parse_dict()
            gb.add_col(colname, col_meta)
            if self._cur is not tokens.COMMA:
                break
            self._consume_i(tokens.COMMA)
        if num_cols == 0:
            raise ZincParseException("No columns defined")
        self._consume_i(tokens.NEWLINE)

        # Grid rows
        while True:
            if self._cur in (tokens.NEWLINE, tokens.EOF):
                break

            # read cells
            cells: List[Scalar] = []
            for i in range(num_cols):
                if self._cur in (tokens.COMMA, tokens.NEWLINE, tokens.EOF):
                    cells.append(NULL)
                else:
                    cells.append(self._parse_val())
                if i + 1 < num_cols:
                    self._consume_i(tokens.COMMA)
            gb.add_row(cells)

            if self._cur is tokens.EOF:
                break
            self._consume_i(tokens.NEWLINE)

        if self._cur is tokens.NEWLINE:
            self._consume_i(tokens.NEWLINE)

        return gb.build()

    def _parse_val(self) -> Scalar:
        if self._cur.ttype is TokenType.RESERVED:
            v = self._cur
            self._consume_t(TokenType.RESERVED)
            if v is tokens.TRUE:
                return BOOL_TRUE
            if v is tokens.FALSE:
                return BOOL_FALSE
            if v is tokens.NULL:
                return NULL
            if v is tokens.MARKER:
                return MARKER
            if v is tokens.NA:
                return NA
            if v is tokens.REMOVE:
                return REMOVE
            if v is tokens.POS_INF:
                return POS_INF
            if v is tokens.NAN:
                return NAN
            raise ZincParseException(f"Unrecognized reserved token {v}")

        if isinstance(self._cur, NumberToken):
            uidx = self._cur.unit_index
            raw = self._cur.val
            units = None
            if uidx > 0:
                raw = self._cur.val[:uidx]
                units = self._cur.val[uidx:]
            try:
                if '.' in raw:
                    qty = float(raw)
                else:
                    qty = int(raw)
            except ValueError:
                raise ZincParseException(
                    f"Invalid numeric token {self._cur}")
            self._consume_t(TokenType.NUMBER)
            return Number(qty, units)

        if self._cur.ttype is TokenType.REF:
            return self._parse_ref()
        if self._cur.ttype is TokenType.STRING:
            return self._parse_string()
        if self._cur.ttype is TokenType.URI:
            return self._parse_uri()
        if self._cur.ttype is TokenType.COORD:
            return self._parse_coord()
        if self._cur.ttype is TokenType.XSTR:
            raise NotImplementedError("XStr support not implemented yet!")

        # -INF
        if self._cur is tokens.MINUS and self._peek.val == "INF":
            self._consume_i(tokens.MINUS)
            self._consume_t(TokenType.ID)
            raise NotImplementedError("No NEG_INF yet!")

        # Nested collections
        if self._cur is tokens.LBRACKET:
            # Could use self._parse_list() down the road, once types work out
            raise NotImplementedError("List-valued Scalars not supported!")
        if self._cur is tokens.LBRACE:
            # Could use self._parse_dict() down the road, once types work out
            raise NotImplementedError("Dict-valued Scalars not supported!")
        if self._cur is tokens.DOUBLELT:
            raise NotImplementedError("Nested grids not supported!")

        # Datetimes
        if self._cur.ttype is TokenType.DATETIME:
            return self._parse_datetime()

        raise ZincParseException(f"Unexpected token: {self._cur}")

    def _parse_coord(self) -> Coord:
        v = self._cur.val
        try:
            lat, lng = v.lstrip('C(').rstrip(')').split(',')
            parsed = Coord(float(lat), float(lng))
        except Exception:
            raise ZincParseException(f"Could not parse {v} as Coord")
        self._consume_t(TokenType.COORD)
        return parsed

    def _parse_xstr(self) -> XStr:
        raise NotImplementedError("XStr support not implemented yet!")

    def _parse_ref(self) -> Ref:
        parts = self._cur.val.split(" ", maxsplit=1)
        self._consume_t(TokenType.REF)
        if len(parts) == 1:
            return Ref(parts[0])
        elif len(parts) == 2:
            return Ref(parts[0], parts[1])
        raise ZincParseException(f"Unparseable ref token {''.join(parts)}")

    def _parse_string(self) -> String:
        val: str = self._cur.val
        self._consume()
        return String(val)

    def _parse_uri(self) -> Uri:
        val: str = self._cur.val
        self._consume()
        return Uri(val)

    def _parse_datetime(self) -> Datetime:
        parts = self._cur.val.split(" ")
        ts = pd.to_datetime(parts[0])
        self._consume()
        if len(parts) == 2:
            # we have a timestamp and a tz
            return Datetime(ts, parts[1])
        if len(parts) == 1:
            return Datetime(ts)
        raise ZincParseException(f"Invalid datetime: {self._cur.val}")

    def _parse_list(self) -> List[Scalar]:
        coll: List[Scalar] = []
        self._consume_i(tokens.LBRACKET)
        while self._cur != tokens.RBRACKET and self._cur != tokens.EOF:
            val = self._parse_val()
            coll.append(val)
            if self._cur is not tokens.COMMA:
                break
            self._consume_i(tokens.COMMA)
        self._consume_i(tokens.RBRACKET)
        return coll

    def _parse_dict(self) -> Dict[str, Scalar]:
        db: Dict[str, Scalar] = {}
        braces = self._cur is tokens.LBRACE
        if braces:
            self._consume_i(tokens.LBRACE)
        while self._cur.ttype is TokenType.ID:
            idstr: str = self._consume_tag_id()
            if not (idstr and idstr[0].islower()):
                raise ZincParseException(f"Invalid dict tag name: {idstr}")
            val: Scalar = MARKER
            if self._cur is tokens.COLON:
                self._consume_i(tokens.COLON)
                val = self._parse_val()
            db[idstr] = val
        if braces:
            self._consume_i(tokens.RBRACE)
        return db

    def _consume_tag_id(self) -> str:
        self._verify_type(TokenType.ID)
        tag_name: str = self._cur.val
        if not (tag_name and tag_name[0].islower()):
            raise ZincParseException(f"Invalid dict tag name: {tag_name}")
        self._consume_t(TokenType.ID)
        return tag_name

    def _consume_str(self) -> String:
        self._verify_type(TokenType.STRING)
        val = String(self._cur.val)
        self._consume_t(TokenType.STRING)
        return val

    def _verify_type(self, expected: TokenType) -> None:
        if self._cur.ttype is not expected:
            raise ZincParseException(
                f"Expected {type(expected)} but found {type(self._cur)}")

    def _verify_eq(self, expected: tokens.Token) -> None:
        if self._cur != expected:
            raise ZincParseException(
                f"Expected {expected} but found {self._cur}")

    def _consume_t(self, expected: TokenType) -> None:
        self._verify_type(expected)
        self._consume()

    def _consume_i(self, expected: tokens.Token) -> None:
        self._verify_eq(expected)
        self._consume()

    def _consume(self) -> None:
        self._cur = self._peek
        self._cur_line = self._peek_line

        self._peek = next(self._tokenizer)
        self._peek_line = self._tokenizer.line
