import pandas as pd  # type: ignore

from os import PathLike
from typing import Optional, Union

from .dtypes import MARKER
from .typing import ColumnInfoType, GridInfoType


YMD_HMS_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _stringify_tag(k, v):
    if v is MARKER:
        return str(k)
    elif isinstance(v, str):
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
        grid_info: A GridInfoType containing, at a minimum, the version
            information of the Grid, and potentially things like the operation
            performed to obtain it.
        column_info: A ColumnInfoType containing metadata about each column.
            Included are details such as what units a column represents, or the
            Point ID associated with the column.
    """

    def __init__(
            self,
            *,
            grid_info: GridInfoType,
            column_info: ColumnInfoType,
            data: pd.DataFrame):
        self.grid_info = grid_info  # type: GridInfoType
        self.column_info = column_info  # type: ColumnInfoType
        self._data = data

    def __repr__(self):
        return (f"Grid<\n"
                + f"grid_info: {self.grid_info.__repr__()}\n"
                + f"column_info: {self.column_info.__repr__()}\n"
                + "data:\n"
                + self._data.__repr__()
                + ">")

    def data(self, squeeze=True) -> Union[pd.DataFrame, pd.Series]:
        """Returns the tabular data in this Grid as a DataFrame or Series.

        Args:
            squeeze: bool, default True
                Whether to return a `pd.Series` if this Grid consists of only
                one column. Otherwise, a `pd.DataFrame` is returned.
        Returns:
            A `pd.DataFrame` or `pd.Series` containing the tabular data in the
            Grid, depending on the value of `squeeze`.
        """
        if len(self._data.columns) == 1 and squeeze:
            return self._data[self._data.columns[0]]
        return self._data

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
        return " ".join(_stringify_tags(self.grid_info))

    def _column_info_str(self):
        cols = []
        for colname, tags in self.column_info.items():
            tagpairs = [colname] + _stringify_tags(tags)
            cols.append(" ".join(tagpairs))
        return ",".join(cols)

    def _zinc_format_data(self):
        df = self._data.copy()
        for i, colinfo in enumerate(self.column_info.values()):
            # Format datetime index as appropriate
            if i == 0:
                # TODO: Don't use a Python for loop! For the life of me, i
                # cannot find a way to do this in Pandas/NumPy. There is no
                # obvious builtin vectorized version.
                df.index = [t.isoformat() for t in df.index.to_pydatetime()]
                if 'tz' in colinfo:
                    df.index += " " + colinfo['tz']
            # Append units to columns where relevant
            elif i >= 1:
                colname = df.columns[i-1]
                if "unit" in colinfo:
                    notna = df[colname].notna()
                    df.loc[notna, colname] = (
                        df.loc[notna, colname].astype(str) + colinfo["unit"])
        return df
