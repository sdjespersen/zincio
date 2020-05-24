import io
import logging
import pandas as pd
import re

from collections import OrderedDict
from pandas.api.types import CategoricalDtype
from typing import Any, Dict, Iterable, Tuple

from .dtypes import MARKER, Datetime, Quantity, Ref
from .grid import Grid
from .typing import FilePathOrBuffer


DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

DEFAULT_TZ = 'Los_Angeles'

ID_COLTAG = "id"
UNIT_COLTAG = "unit"
KIND_COLTAG = "kind"
ENUM_COLTAG = "enum"

NUMBER_KIND = "Number"
STRING_KIND = "Str"

# We don't want to be in the business of maintaining this list; it's solely for
# heuristically inferring the unit type of a series that didn't come along with
# some metadata.
NUMERIC_UNIT_SUFFIXES = ("°F", "°C", "%", "cfm", "kW")

QUANTITY_TAGS = ('curVal', 'writeVal')
FLOAT_VALUED_TAGS = ('precision', 'writeLevel')
INTEGER_VALUED_TAGS = ('hisLimit',)


class ZincParseException(Exception):
    pass


class ZincErrorGridException(Exception):
    pass


def read_zinc(filepath_or_buffer: FilePathOrBuffer) -> Grid:
    """Reads utf-8 encoded Zinc file or buffer to a Grid."""
    with _handle_buffer(filepath_or_buffer) as f:
        gridinfo_raw = f.readline().rstrip("\n")
        colinfo_raw = f.readline().rstrip("\n")
        if not gridinfo_raw or not colinfo_raw:
            raise ZincParseException("Malformed input")
        grid_info = _parse_zinc_grid_info(gridinfo_raw)
        column_info = _parse_zinc_column_info(colinfo_raw)
        try:
            # Zinc can indicate "null" with "N"; in pandas-land, this is not
            # distinct from "NaN", so we convert
            data = pd.read_csv(f, header=None, na_values='N')
        except pd.errors.EmptyDataError:
            logging.warn("Empty data")
    renaming = {}
    for i, (k, v) in enumerate(column_info.items()):
        if i > 0:
            if ID_COLTAG in v:
                renaming[i] = str(v[ID_COLTAG])
            else:
                renaming[i] = k
    data.rename(columns=renaming, inplace=True)
    for i, col in enumerate(column_info):
        colinfo = column_info[col]
        cname = data.columns[i]
        # i == 0 corresponds to the index; leave until end
        if i > 0:
            data[cname] = _sanitize_zinc_series(data[cname], colinfo)
    _set_datetime_index(data, column_info['ts'])
    return Grid(data=data, column_info=column_info, grid_info=grid_info)


def _handle_buffer(filepath_or_buffer):
    if isinstance(filepath_or_buffer, io.StringIO):
        return filepath_or_buffer
    return open(filepath_or_buffer, encoding="utf-8")


def _parse_zinc_grid_info(gridinfo: str) -> Dict[str, str]:
    tags = _parse_tags(_split_tags(gridinfo))
    if 'ver' not in tags:
        raise ZincParseException("Invalid version header!")
    if 'err' in tags:
        raise ZincErrorGridException(gridinfo)
    return tags


def _parse_zinc_column_info(header: str) -> Dict[str, Dict[str, Any]]:
    column_info = OrderedDict()  # type: OrderedDict[str, Dict[str, Any]]
    for col in _split_columns(header):
        toks = _split_tags(col)
        colname, v = next(toks)
        assert v == MARKER
        column_info[colname] = _parse_tags(toks)
    return column_info


def _split_columns(s):
    i, j = -1, 0
    inside_quotes = False
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 1
        elif c == '"':
            inside_quotes = not inside_quotes
        elif c == "," and not inside_quotes:
            yield s[i+1:j]
            i = j
        j += 1
    # don't forget the last one!
    yield s[i+1:j]


def _split_tags(s):
    i, j = -1, 0
    inside_quotes, inside_ref = False, False
    inside_numeric, inside_timezone = False, False
    tag = None
    while j < len(s):
        c = s[j]
        if c == "\\":
            # always skip escaped chars
            j += 1
        elif tag is None:
            # we are tokenizing a tag
            if c == ':':
                # tag with nontrivial value found
                tag = s[i+1:j]
                i = j
                # lookahead to see if ref
                if s[j+1] == '@':
                    j += 1
                    inside_ref = True
                elif s[j+1].isdigit():
                    inside_numeric = True
            elif c == " ":
                # this is a marker tag; immediately yield
                yield s[i+1:j], MARKER
                i = j
        else:
            # we are tokenizing a value
            if c == '"' and inside_quotes and inside_ref:
                # this is the end of a ref!
                j += 1
                assert j == len(s) or s[j] == " "
                yield tag, s[i+1:j]
                i = j
                tag = None
                inside_quotes, inside_ref = False, False
            elif c == '"':
                # this is a normal quote
                inside_quotes = not inside_quotes
            elif c == " " and inside_timezone:
                # finished tokenizing a datetime with timezone
                yield tag, s[i+1:j]
                i = j
                tag = None
                inside_numeric, inside_timezone = False, False
            elif c == " " and inside_numeric and _expect_timezone(s, i, j):
                # If a timezone is coming up, this space should not be
                # interpreted as a token separator!
                inside_timezone = True
            elif c == " " and not (inside_quotes or inside_ref):
                # found a legit value
                yield tag, s[i+1:j]
                i = j
                tag = None
                inside_numeric = False
        j += 1
    # we've reached the end of the string
    if tag is None:
        yield s[i+1:j], MARKER
    else:
        yield tag, s[i+1:j]


def _expect_timezone(s, i, j):
    """Return whether or not the next substring is a timezone."""
    is_dt_str = (DATETIME_PATTERN.search(s[i+1:j]) is not None)
    utc_is_next = (j + 4 < len(s) and s[j+1:j+4] == 'UTC')
    return is_dt_str and (utc_is_next or not s[i+1:j].endswith('Z'))


def _parse_tags(
        tokens: Iterable[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
    result = OrderedDict()  # type: Dict[str, Any]
    for k, v in tokens:
        if v is MARKER:
            result[k] = v
        elif DATETIME_PATTERN.match(v):
            splits = v.split(" ", maxsplit=1)
            assert len(splits) > 0
            dt = pd.to_datetime(splits[0])
            if len(splits) == 2:
                result[k] = Datetime(dt, splits[1])
            else:
                result[k] = Datetime(dt)
        else:
            v = v.strip('"')
            if v.startswith('@'):
                # this is a ref
                refid, refname = v.split(' ', maxsplit=1)
                result[k] = Ref(refid.lstrip('@'), refname.strip('"'))
            else:
                result[k] = v
    # now that we have all the info, we can parse relevant values
    unit = result.get(UNIT_COLTAG, None)
    for tag in QUANTITY_TAGS:
        if tag in result:
            if unit is not None:
                val = result[tag]
                result[tag] = Quantity(float(val.rstrip(unit)), unit)
    for tag in FLOAT_VALUED_TAGS:
        if tag in result:
            result[tag] = float(result[tag])
    for tag in INTEGER_VALUED_TAGS:
        if tag in result:
            result[tag] = int(result[tag])
    return result


def _sanitize_zinc_series(
        series: pd.Series, colinfo: Dict[str, Any]) -> pd.Series:
    if series.isna().all():
        # we are powerless in this situation
        return series
    elif colinfo:
        kind = colinfo[KIND_COLTAG]
        if kind == NUMBER_KIND:
            if UNIT_COLTAG in colinfo:
                # Now we should be able to safely strip units
                # Parse as numeric type
                unitless = series.str.rstrip(colinfo[UNIT_COLTAG])
                return pd.to_numeric(unitless)
            else:
                return series
        elif ENUM_COLTAG in colinfo:
            cat_type = CategoricalDtype(
                categories=colinfo[ENUM_COLTAG].split(","))
            return series.astype(cat_type)
        elif kind != STRING_KIND:
            raise ZincParseException(f"Unrecognized kind {kind}")
    else:
        logging.debug("No column headers, heuristically inferring type")
        for suffix in NUMERIC_UNIT_SUFFIXES:
            if series[0].endswith(suffix):
                return pd.to_numeric(series.str.rstrip(suffix))
    return series


def _set_datetime_index(data, colinfo):
    tz = colinfo.get('tz', DEFAULT_TZ)
    data.index = pd.DatetimeIndex(data[0].str.rstrip(tz).str.rstrip())
    data.index.name = 'ts'
    data.drop([0], axis=1, inplace=True)
