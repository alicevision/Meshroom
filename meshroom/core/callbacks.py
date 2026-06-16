"""
Callback registry system for Meshroom.

This module provides a mechanism to register, query, and trigger callbacks
that can execute before certain actions (e.g., save, saveAs).

Usage:
    from meshroom.core.callbacks import registerCallback, getRegisteredCallback, triggerCallback

    # Register a callback
    def mySaveCallback(*args, **kwargs):
        # ... do something ...
        return result

    registerCallback("save", mySaveCallback)

    # Check if a callback is registered
    cb = getRegisteredCallback("save")  # returns the callable or None

    # Trigger the callback
    result = triggerCallback("save", arg1, arg2)
"""

import logging

logger = logging.getLogger(__name__)

# Internal registry: maps callback names to callables
_callbacks = {}


def registerCallback(name, callback):
    """
    Register a callback with the given name.

    Args:
        name (str): The name/key for the callback (e.g., "save").
        callback (callable): The function to be called when the callback is triggered.

    Raises:
        ValueError: If `name` is empty or `callback` is not callable.
    """
    if not name:
        raise ValueError("Callback name must not be empty.")
    if not callable(callback):
        raise ValueError(f"Callback for '{name}' must be callable.")
    if name in _callbacks:
        logger.warning(f"Overwriting existing callback for '{name}'.")
    _callbacks[name] = callback
    logger.debug(f"Callback registered: '{name}'")


def unregisterCallback(name):
    """
    Unregister a callback by name.

    Args:
        name (str): The name of the callback to remove.

    Returns:
        bool: True if a callback was removed, False if none was found.
    """
    if name in _callbacks:
        del _callbacks[name]
        logger.debug(f"Callback unregistered: '{name}'")
        return True
    return False


def getRegisteredCallback(name):
    """
    Get a registered callback by name.

    Args:
        name (str): The name of the callback to retrieve.

    Returns:
        callable or None: The registered callback, or None if not found.
    """
    return _callbacks.get(name, None)


def triggerCallback(name, *args, **kwargs):
    """
    Trigger a registered callback by name.

    Args:
        name (str): The name of the callback to trigger.
        *args: Positional arguments to pass to the callback.
        **kwargs: Keyword arguments to pass to the callback.

    Returns:
        The result of the callback, or None if no callback is registered for `name`.
    """
    callback = _callbacks.get(name, None)
    if callback is None:
        logger.debug(f"No callback registered for '{name}', skipping.")
        return None
    logger.debug(f"Triggering callback '{name}' with args={args}, kwargs={kwargs}")
    try:
        return callback(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error while executing callback '{name}': {e}")
        raise


def clearCallbacks():
    """Clear all registered callbacks. Useful for testing."""
    _callbacks.clear()


# Convenience decorator-style function
def REGISTER_CALLBACK(name):
    """
    Decorator to register a function as a callback.

    Usage:
        @REGISTER_CALLBACK(name="save")
        def my_save_callback(*args, **kwargs):
            ...
    """
    def decorator(func):
        registerCallback(name, func)
        return func
    return decorator
