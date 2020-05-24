import pandas as pd

from collections import OrderedDict


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
                + f"grid_info: {self.grid_info}\n"
                + f"column_info: {self.column_info}\n"
                + "data:\n"
                + self.data.__repr__()
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
