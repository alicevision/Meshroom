"""Utilities for marking function parameters as deprecated."""

import warnings
import logging


def depreciateParam(paramToDepreciate, msg):
    """Decorator factory that emits a deprecation warning when a specific keyword argument is used.

    Use this to gracefully phase out function parameters by warning callers
    that a particular keyword argument is deprecated, while still allowing
    the decorated function to execute normally.

    Args:
        paramToDepreciate (str): The name of the keyword argument to flag as deprecated.
        msg (str): A warning message template that will be formatted with the keyword
            arguments passed to the decorated function (using ``str.format(**kwargs)``).

    Returns:
        callable: A decorator that wraps the target function with deprecation checks.

    Example:
        >>> @depreciateParam("oldArg", "'{oldArg}' is deprecated, use 'newArg' instead")
        ... def my_func(newArg=None, oldArg=None):
        ...     pass
        >>> my_func(oldArg="value")  # emits DeprecationWarning
    """
    def decorator(function):
        def wrapper(*args, **kwargs):
            if paramToDepreciate in kwargs.keys():
                warnings.warn(msg.format(**kwargs), DeprecationWarning)
                logging.warn(DeprecationWarning(msg.format(**kwargs)))
            return function(*args, **kwargs)
        return wrapper
    return decorator
