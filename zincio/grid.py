import logging
import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from os import PathLike
from pandas.api.types import CategoricalDtype  # type: ignore
from typing import Any, Dict, List, Optional, Union

from .dtypes import AbstractScalar, Boolean, Number, String, MARKER, NULL, NA


ID_COLTAG = 'id'
KIND_COLTAG = 'kind'
UNIT_COLTAG = 'unit'
ENUM_COLTAG = 'enum'

NUMBER_KIND = String("Number")
STRING_KIND = String("Str")


def _stringify_tag(k, v):
    if v is MARKER:
        return str(k)
    elif isinstance(v, String):
        return f"{k}:\"{v}\""
    else:
        return f"{k}:{v}"


def _stringify_tags(tags):
    return [_stringify_tag(k, v) for k, v in tags.items()]


class Grid:
    """A tabular data frame for Project Haystack.

    A Grid essentially consists of three parts:

    - Grid-level metadata
    - Column-level metadata
    - Tabular data

    Most of the time, for instance in the data analysis setting, we are
    interested primarily in the numerical values contained in the tabular data,
    and less interested in the column/grid metadata. To retrieve the tabular
    data as a Pandas DataFrame or Series, simply call `.data()`.

    For an extended description of a Project Haystack Grid, see
    https://project-haystack.org/doc/Grids. For a full description of the Zinc
    format, see https://project-haystack.org/doc/Zinc.

    Attributes:
        grid_info: A Dict[str, Any] containing, at a minimum, the version
            information of the Grid, and potentially things like the operation
            performed to obtain it.
        column_info: A Dict[str, Dict[str, Any]] containing metadata about each
            column. Included are details such as what units a column
            represents, or the Point ID associated with the column.
    """

    def __init__(
            self,
            *,
            version: int,
            grid_info: Dict[str, Any],
            column_info: Dict[str, Dict[str, Any]],
            data: pd.DataFrame):
        self.version = version  # type: int
        self.grid_info = grid_info  # type: Dict[str, Any]
        self.column_info = column_info  # type: Dict[str, Dict[str, Any]]
        self.data = data

    def __repr__(self):
        return (f"Grid<\n"
                + f"grid_info: {self.grid_info.__repr__()}\n"
                + f"column_info: {self.column_info.__repr__()}\n"
                + "data:\n"
                + self.data.__repr__()
                + ">")

    def to_pandas(self, squeeze=True) -> Union[pd.DataFrame, pd.Series]:
        """Returns the tabular data in this Grid as a DataFrame or Series.

        Args:
            squeeze: bool, default True
                Whether to return a `pd.Series` if this Grid consists of only
                one column. Otherwise, a `pd.DataFrame` is returned.
        Returns:
            A `pd.DataFrame` or `pd.Series` containing the tabular data in the
            Grid, depending on the value of `squeeze`.
        """
        if len(self.data.columns) == 1 and squeeze:
            return self.data[self.data.columns[0]]
        return self.data

    def to_zinc(self, path: Optional[PathLike] = None) -> Optional[str]:
        """Writes the object to a Zinc-formatted file.

        Args:
            path: str or file handle, default None
                File path or object. If None is provided, the result is
                returned as a string. Otherwise, object is written to file.
        Returns:
            The Zinc-formatted string representation of the grid if path is not
            None, otherwise None.
        """
        gridinfostr = self._grid_info_str()
        columninfostr = self._column_info_str()
        df = self._zinc_format_data()
        if path is not None:
            with open(path, "w", encoding="utf-8") as f:
                f.write(gridinfostr + "\n")
                f.write(columninfostr + "\n")
                df.to_csv(f, mode="a", header=False)
            return None
        return "\n".join([gridinfostr, columninfostr, df.to_csv(header=False)])

    def _grid_info_str(self):
        return " ".join([
            f'ver:"{self.version}.0"'] + _stringify_tags(self.grid_info))

    def _column_info_str(self):
        cols = []
        for colname, tags in self.column_info.items():
            tagpairs = [colname] + _stringify_tags(tags)
            cols.append(" ".join(tagpairs))
        return ",".join(cols)

    def _zinc_format_data(self):
        df = self.data.copy()
        for i, colinfo in enumerate(self.column_info.values()):
            # Format datetime index as appropriate
            if i == 0:
                # TODO: Don't use a Python for loop! For the life of me, i
                # cannot find a way to do this in Pandas/NumPy. There is no
                # obvious builtin vectorized version.
                df.index = [t.isoformat() for t in df.index.to_pydatetime()]
                if 'tz' in colinfo:
                    df.index += " " + str(colinfo['tz'])
            # Append units to columns where relevant
            elif i >= 1:
                colname = df.columns[i-1]
                if "unit" in colinfo:
                    notna = df[colname].notna()
                    unit = str(colinfo["unit"])
                    df.loc[notna, colname] = (
                        df.loc[notna, colname].astype(str) + unit)
        return df


class GridBuilder:
    """Builder for Grid.

    Collects all necessary information before constructing the Grid.
    """

    def __init__(self, version: int):
        self.version = version
        self.grid_meta = None
        self.col_meta: Dict[str, AbstractScalar] = {}
        self.cols: Dict[str, List[AbstractScalar]] = {}

    def add_meta(self, grid_meta: Dict[str, Any]):
        self.grid_meta = grid_meta

    def add_col(self, colname: str, col: Dict[str, Dict[str, Any]]):
        self.col_meta[colname] = col
        self.cols[colname] = []

    def add_row(self, row: List[AbstractScalar]):
        for k, v in zip(self.cols, row):
            self.cols[k].append(v)

    def build(self):
        idx = [x.val for x in self.cols.pop('ts')]
        df = pd.DataFrame(data=self.cols, index=idx)
        df.index.name = 'ts'
        # Rename columns with ID tag, if available
        renaming = {}
        for col in df.columns:
            v = self.col_meta[col]
            if ID_COLTAG in v:
                renaming[col] = str(v[ID_COLTAG])
        df.rename(columns=renaming, inplace=True)
        for i, col in enumerate(self.col_meta):
            # i == 0 corresponds to the index; skip
            if i > 0:
                colinfo = self.col_meta[col]
                cname = df.columns[i-1]
                df[cname] = _sanitize_series(df[cname], colinfo)
        return Grid(
            version=self.version,
            grid_info=self.grid_meta,
            column_info=self.col_meta,
            data=df)


def _pandasify(val: AbstractScalar) -> Any:
    if val is None or val in (NULL, NA):
        return np.nan
    if isinstance(val, Number) or isinstance(val, String):
        return val.value
    return str(val)


def _pandasify_bool(val: AbstractScalar) -> Any:
    if isinstance(val, Boolean):
        return val.value
    if val is NULL:
        return None
    return val


def _sanitize_series(series: pd.Series, colinfo: Dict[str, Any]) -> pd.Series:
    # 1. Ascertain dtype of Series
    # 2. Apply pandasify to series
    # 3. Reinterpret as dtype
    kind = colinfo.get(KIND_COLTAG, None)
    if kind is not None:
        if kind == NUMBER_KIND:
            return pd.to_numeric(series.apply(_pandasify))
        elif ENUM_COLTAG in colinfo:
            cat_type = CategoricalDtype(
                categories=str(colinfo[ENUM_COLTAG]).split(","))
            return series.apply(_pandasify).astype(cat_type)
    else:
        logging.debug("No column headers, heuristically inferring type")
        sample = series[:1000].dropna()
        if not len(sample):
            logging.debug("No non-NA values from which to infer type")
            return series
        for v in sample:
            if isinstance(v, Number):
                return pd.to_numeric(series.apply(_pandasify))
            if isinstance(v, Boolean):
                return series.apply(_pandasify_bool)
    return series
