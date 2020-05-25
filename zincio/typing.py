from os import PathLike
from typing import Any, Dict, Union

FilePathOrBuffer = Union[str, bytes, int, PathLike]
# Dict should be OrderedDict, but Python isn't there yet
ColumnInfoType = Dict[str, Dict[str, Any]]
# Dict should be OrderedDict, but Python isn't there yet
GridInfoType = Dict[str, Any]
