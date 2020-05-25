"""Zinc data types."""

import pandas as pd  # type: ignore

from typing import Optional, Union


class MarkerType:
    """Type of the Zinc Marker."""

    def __repr__(self):
        return 'MARKER'


MARKER = MarkerType()


class Datetime:
    def __init__(self, dt: Union[str, pd.Timestamp], tz: Optional[str] = None):
        self.dt = dt
        if isinstance(self.dt, str):
            self.dt = pd.to_datetime(self.dt)
        self.tz = tz

    def __repr__(self):
        return f"{type(self).__name__}({self.dt.isoformat()}, \"{self.tz}\")"

    def __str__(self):
        s = self.dt.isoformat()
        if self.tz is not None:
            s += " " + self.tz
        return s

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if other is self:
            return True
        return self.dt == other.dt and self.tz == other.tz


class Quantity:
    def __init__(self, value: Union[float, int], units: Optional[str] = None):
        self.value = value
        self.units = units

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if other is self:
            return True
        return self.value == other.value and self.units == other.units

    def __repr__(self):
        return f"{type(self).__name__}({self.value}, \"{self.units}\")"

    def __str__(self):
        s = str(self.value)
        if self.units is not None:
            s += str(self.units)
        return s


class Ref:
    def __init__(self, uid: str, name: str):
        self.uid = uid
        self.name = name

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if other is self:
            return True
        return self.uid == other.uid and self.name == other.name

    def __repr__(self):
        return f"{type(self).__name__}(\"{self.uid}\", \"{self.name}\")"

    def __str__(self):
        s = "@" + self.uid
        if self.name is not None:
            s += f' "{self.name}"'
        return s


class URI:
    pass
