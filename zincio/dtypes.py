"""Zinc data types."""

import pandas as pd  # type: ignore

from typing import Any, Optional, Union


class AbstractScalar:
    pass


class SentinelScalar(AbstractScalar):
    """A valueless scalar whose meaning is found entirely in its type."""

    def __repr__(self):
        return type(self).__name__


class Scalar(AbstractScalar):

    def __init__(self, value: Any):
        self.value = value

    def __repr__(self):
        return f"{type(self).__name__}({self.value})"

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if other is self:
            return True
        return self.value == other.value


class Null(SentinelScalar):
    """Type of the Zinc null indicator."""
    pass


class Marker(SentinelScalar):
    """Type of the Zinc marker."""
    pass


class Remove(SentinelScalar):
    """Type of the Zinc Remove marker."""
    pass


class Na(SentinelScalar):
    """Type of the Zinc NA indicator."""
    pass


NULL = Null()
MARKER = Marker()
REMOVE = Remove()
NA = Na()


class Boolean(Scalar):
    pass


BOOL_TRUE = Boolean(True)
BOOL_FALSE = Boolean(False)


class Datetime(Scalar):
    def __init__(self, val: pd.Timestamp, tz: Optional[str] = None):
        self.val = val
        self.tz = tz

    def __repr__(self):
        return f"{type(self).__name__}({self.val.isoformat()}, \"{self.tz}\")"

    def __str__(self):
        s = self.val.isoformat()
        if self.tz is not None:
            s += " " + self.tz
        return s

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if other is self:
            return True
        return self.val == other.val and self.tz == other.tz


class Number(Scalar):
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


class Coord(Scalar):

    def __init__(self, lat: float, lng: float):
        self.lat = lat
        self.lng = lng

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if other is self:
            return True
        return self.lat == other.lat and self.lng == other.lng


class Ref(Scalar):

    def __init__(self, uid: str, display_name: Optional[str] = None):
        self.uid = uid
        self.display_name = None
        if display_name:
            self.display_name = display_name.strip('"')

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if other is self:
            return True
        return (
            self.uid == other.uid and self.display_name == other.display_name)

    def __repr__(self):
        return f"{type(self).__name__}({self.uid}, \"{self.display_name}\")"

    def __str__(self):
        s = '@' + self.uid
        if self.display_name is not None:
            s += f' "{self.display_name}"'
        return s


class Uri(Scalar):
    pass


class String(Scalar):
    pass


class XStr(Scalar):
    pass


class Id(Scalar):
    pass
