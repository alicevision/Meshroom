
try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str, bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring

try:
    # Import ABC from collections.abc in Python 3.4+
    from collections.abc import Sequence, Iterable
except ImportError:
    # Import ABC from collections in Python 2 support
    from collections import Sequence, Iterable
