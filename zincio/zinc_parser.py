import io
from os import PathLike
import pandas as pd
from typing import Dict, IO, List, Optional, Union

from .dtypes import (
    NULL,
    MARKER,
    REMOVE,
    NA,
    BOOL_TRUE,
    BOOL_FALSE,
    AbstractScalar,
    Id,
    Coord,
    Datetime,
    Marker,
    Number,
    Ref,
    String,
    XStr,
)
from .grid import Grid, GridBuilder
from . import tokens
from .tokens import TokenType
from .zinc_tokenizer import ZincTokenizer

# Type alias
FilePathOrBuffer = Union[str, bytes, int, PathLike]


class ZincParseException(Exception):
    pass


class ZincErrorGridException(Exception):
    pass


def parse(s: str) -> Grid:
    """Parses utf-8 encoded string to a Grid.

    Arguments:
        s: str, utf-8 encoded string to be parsed.
    """
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
        self._tokenizer = tokenizer
        self._cur = None
        self._peek = None
        self._cur_line = 0
        self._peek_line = 0
        self._version = 3
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

        # TODO: Support nested Grids. Actually, i'll probably never do that.
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
        num_cols = 0  # type: int
        while self._cur.ttype is TokenType.ID:
            num_cols += 1
            colname = self._consume_tag_name()
            col_meta = {}
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
            cells = []
            for i in range(num_cols):
                if self._cur in (tokens.COMMA, tokens.NEWLINE, tokens.EOF):
                    cells.append(None)
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

    def _parse_val(self) -> AbstractScalar:
        # If it's an ID
        if self._cur.ttype is TokenType.ID:
            id_str = self._cur.val
            self._consume_t(TokenType.ID)
            # check for coord or xstr
            if self._cur is tokens.LPAREN:
                if self._peek.ttype is TokenType.NUMBER:
                    return self._parse_coord(id_str)
                else:
                    return self._parse_xstr(id_str)
            raise ZincParseException(f"Unexpected identifier: {id_str}")

        # If it's a reserved keyword
        if self._cur.ttype is TokenType.RESERVED:
            v = self._cur.val
            self._consume_t(TokenType.RESERVED)
            if v == "T":
                return BOOL_TRUE
            if v == "F":
                return BOOL_FALSE
            if v == "N":
                return NULL
            if v == "M":
                return MARKER
            if v == "NA":
                return NA
            if v == "R":
                return REMOVE
            raise ZincParseException(f"Unrecognized reserved token {v}")

        if self._cur.ttype is TokenType.NUMBER:
            # TODO: Support "NaN", "INF"
            uidx = self._cur.unit_index
            raw = self._cur.val
            units = None
            if uidx > 0:
                raw = self._cur.val[:uidx]
                units = self._cur.val[uidx:]
            try:
                qty = float(raw)
            except ValueError:
                raise ZincParseException(
                    f"Invalid numeric token {self._cur}")
            self._consume_t(TokenType.NUMBER)
            return Number(qty, units)

        if self._cur.ttype is TokenType.REF:
            return self._parse_ref()
        if self._cur.ttype is TokenType.STRING:
            return self._parse_string()

        # -INF
        if self._cur is tokens.MINUS and self._peek.val == "INF":
            self._consume_i(tokens.MINUS)
            self._consume_i(tokens.ID)
            raise NotImplementedError("No NEG_INF yet!")

        # Nested collections
        if self._cur is tokens.LBRACKET:
            return self._parse_list()
        if self._cur is tokens.LBRACE:
            return self._parse_dict()
        if self._cur is tokens.DOUBLELT:
            raise NotImplementedError("Nested grids not supported!")

        # Datetimes
        if self._cur.ttype is TokenType.DATETIME:
            return self._parse_datetime()

        raise ZincParseException(f"Unexpected token: {self._cur}")

    def _parse_coord(self, id_str: str) -> Coord:
        if id_str != "C":
            raise ZincParseException(f"Expected 'C' for coord, not {id_str}")
        self._consume_i(tokens.LPAREN)
        lat = self._consume_num()
        self._consume_i(tokens.COMMA)
        lng = self._consume_num()
        self._consume_i(tokens.RPAREN)
        return Coord(lat.val, lng.val)

    def _parse_xstr(self) -> XStr:
        # {
        # if (!Character.isUpperCase(id.charAt(0)))
        #   throw err("Invalid XStr type: " + id);
        # consume(HaystackToken.lparen);
        # if (this.version < 3 && "Bin".equals(id)) return parseBinObsolete();
        # String val = consumeStr();
        # consume(HaystackToken.rparen);
        # return HXStr.decode(id, val);
        # }
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
        val = self._cur.val
        self._consume()
        return String(val)

    def _parse_datetime(self) -> Datetime:
        parts = self._cur.val.split(" ")
        ts = pd.to_datetime(parts[0])
        self._consume()
        if len(parts) == 2:
            # we have a timestamp and a tz
            return Datetime(ts, parts[1])
        if len(parts) == 1:
            return Datetime(ts, None)
        raise ZincParseException(f"Invalid datetime: {self._cur.val}")

    def _parse_list(self) -> List[AbstractScalar]:
        coll = []  # type: List[AbstractScalar]
        self._consume(tokens.LBRACKET)
        while self._cur != tokens.RBRACKET and self._cur != tokens.EOF:
            val = self._parse_val()
            coll.append(val)
            if self._cur is not tokens.COMMA:
                break
            self._consume(tokens.COMMA)
        self._consume(tokens.RBRACKET)
        return coll

    def _parse_dict(self) -> Dict:
        db = {}
        braces = self._cur is tokens.LBRACE
        if braces:
            self._consume_i(tokens.LBRACE)
        while self._cur.ttype is TokenType.ID:
            idstr = self._consume_tag_name()  # type: str
            if not (idstr and idstr[0].islower()):
                raise ZincParseException(f"Invalid dict tag name: {idstr}")

            val = MARKER  # type: Marker
            if self._cur is tokens.COLON:
                self._consume_i(tokens.COLON)
                val = self._parse_val()
            db[idstr] = val
        if braces:
            self._consume_i(tokens.RBRACE)
        return db

    def _consume_tag_name(self) -> Id:
        self._verify_type(TokenType.ID)
        tag_name = self._cur.val
        if not (tag_name and tag_name[0].islower()):
            raise ZincParseException(f"Invalid dict tag name: {tag_name}")
        self._consume_t(TokenType.ID)
        return tag_name

    def _consume_num(self) -> Number:
        self._verify_type(TokenType.NUMBER)
        val = self._cur.val
        self._consume_t(TokenType.NUMBER)
        return val

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
