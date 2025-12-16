"""
This module provides an abstraction around standard non-gui Qt notions (like Signal/Slot),
so it can be used in python-only without the dependency to Qt.

Warning: A call to `init(Backend.XXX)` is required to choose the backend before using this module.
"""

from enum import Enum


class Backend(Enum):
    STANDALONE = 1
    PYSIDE = 2


DictModel = None
ListModel = None
Slot = None
Signal = None
Property = None
BaseObject = None
Variant = None
VariantList = None
JSValue = None


def init(backend):
    global DictModel, ListModel, Slot, Signal, Property, BaseObject, Variant, VariantList, JSValue
    if backend == Backend.PYSIDE:
        # PySide types
        from .qt import DictModel, ListModel, Slot, Signal, Property, BaseObject, Variant, VariantList, JSValue
    elif backend == Backend.STANDALONE:
        # Core types
        from .core import DictModel, ListModel, Slot, Signal, Property, BaseObject, Variant, VariantList, JSValue


def strtobool(val: str):
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))


# Default initialization
init(Backend.STANDALONE)
