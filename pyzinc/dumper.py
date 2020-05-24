"""Zinc output writing."""

import io

from pathlib import Path
from typing import IO, Union, AnyStr

from .grid import Grid


def dump(grid: Grid, filepath_or_buffer: Union[str, Path, IO[AnyStr]]):
    """Dumps a grid to the given output file path or buffer."""
    with _handle_open_buffer(filepath_or_buffer) as f:
        f.write(str(grid.grid_info))
        f.write("\n")
        f.write(str(grid.column_info))
        f.write("\n")
        print(f.read())
        grid.data(squeeze=False).to_csv(f)


def _handle_open_buffer(filepath_or_buffer):
    if isinstance(filepath_or_buffer, io.StringIO):
        return filepath_or_buffer
    return open(filepath_or_buffer, "w", encoding="utf-8")
