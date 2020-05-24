import io
import pandas as pd

from collections import OrderedDict
from typing import Optional

from .dtypes import MARKER
from .typing import FilePathOrBuffer


YMD_HMS_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _write_handle(path_or_buf: FilePathOrBuffer):
    if isinstance(path_or_buf, io.StringIO):
        return path_or_buf
    return open(path_or_buf, "w", encoding="utf-8")


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
    """

    def __init__(
            self,
            *,
            grid_info: str,
            column_info: OrderedDict,
            data: pd.DataFrame):
        self.grid_info = grid_info
        self.column_info = column_info
        self._data = data

    def __repr__(self):
        return (f"Grid<\n"
                + f"grid_info: {self.grid_info.__repr__()}\n"
                + f"column_info: {self.column_info.__repr__()}\n"
                + "data:\n"
                + self._data.__repr__()
                + ">")

    def data(self, squeeze=True):
        """Returns the tabular data in this Grid as a DataFrame or Series.

        Args:
            squeeze: bool, Whether to return a `pd.Series` if this Grid
                consists of only one column. Otherwise, a `pd.DataFrame` is
                returned.
        """
        if len(self._data.columns) == 1 and squeeze:
            return self._data[self._data.columns[0]]
        return self._data

    def to_zinc(
            self,
            path_or_buf: Optional[FilePathOrBuffer] = None) -> Optional[str]:
        gridinfostr = self._grid_info_str()
        columninfostr = self._column_info_str()
        df = self._zinc_format_data()
        if path_or_buf is not None:
            with _write_handle(path_or_buf) as f:
                f.write(gridinfostr + "\n")
                f.write(columninfostr + "\n")
                df.to_csv(f, mode="a", header=False)
        return "\n".join([gridinfostr, columninfostr, df.to_csv(header=False)])

    def _grid_info_str(self):
        tags = []
        for k, v in self.grid_info.items():
            if v is MARKER:
                tags.append(str(k))
            elif isinstance(v, str):
                tags.append(f"{k}:\"{v}\"")
            else:
                tags.append(f"{k}:{v}")
        return " ".join(tags)

    def _column_info_str(self):
        cols = []
        for colname, tags in self.column_info.items():
            tagpairs = [colname]
            for k, v in tags.items():
                if v is MARKER:
                    tagpairs.append(str(k))
                elif isinstance(v, str):
                    tagpairs.append(f"{k}:\"{v}\"")
                else:
                    tagpairs.append(f"{k}:{v}")
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
