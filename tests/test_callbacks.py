"""Tests for the callback registry system."""

import pytest
from meshroom.core.callbacks import (
    registerCallback,
    unregisterCallback,
    getRegisteredCallback,
    triggerCallback,
    clearCallbacks,
    REGISTER_CALLBACK,
)


@pytest.fixture(autouse=True)
def clean_callbacks():
    """Ensure callbacks are cleared before and after each test."""
    clearCallbacks()
    yield
    clearCallbacks()


def test_register_and_get_callback():
    """Test that a callback can be registered and retrieved."""
    def my_cb():
        return "hello"

    registerCallback("test", my_cb)
    assert getRegisteredCallback("test") is my_cb


def test_get_unregistered_callback():
    """Test that getting an unregistered callback returns None."""
    assert getRegisteredCallback("nonexistent") is None


def test_trigger_callback():
    """Test that a registered callback can be triggered."""
    def my_cb(x, y):
        return x + y

    registerCallback("add", my_cb)
    result = triggerCallback("add", 3, 4)
    assert result == 7


def test_trigger_unregistered_callback():
    """Test that triggering an unregistered callback returns None."""
    result = triggerCallback("nonexistent", 1, 2)
    assert result is None


def test_trigger_callback_with_kwargs():
    """Test that kwargs are passed through to the callback."""
    def my_cb(*args, **kwargs):
        return {"args": args, "kwargs": kwargs}

    registerCallback("kw", my_cb)
    result = triggerCallback("kw", 1, key="value")
    assert result == {"args": (1,), "kwargs": {"key": "value"}}


def test_unregister_callback():
    """Test that a callback can be unregistered."""
    registerCallback("test", lambda: None)
    assert unregisterCallback("test") is True
    assert getRegisteredCallback("test") is None


def test_unregister_nonexistent_callback():
    """Test that unregistering a non-existent callback returns False."""
    assert unregisterCallback("nonexistent") is False


def test_overwrite_callback():
    """Test that registering a callback with the same name overwrites the previous one."""
    registerCallback("test", lambda: "first")
    registerCallback("test", lambda: "second")
    result = triggerCallback("test")
    assert result == "second"


def test_register_callback_empty_name_raises():
    """Test that registering with an empty name raises ValueError."""
    with pytest.raises(ValueError):
        registerCallback("", lambda: None)


def test_register_callback_non_callable_raises():
    """Test that registering a non-callable raises ValueError."""
    with pytest.raises(ValueError):
        registerCallback("test", "not_callable")


def test_trigger_callback_propagates_exceptions():
    """Test that exceptions from the callback are propagated."""
    def bad_cb():
        raise RuntimeError("test error")

    registerCallback("bad", bad_cb)
    with pytest.raises(RuntimeError, match="test error"):
        triggerCallback("bad")


def test_register_callback_decorator():
    """Test the REGISTER_CALLBACK decorator."""
    @REGISTER_CALLBACK(name="decorated")
    def my_decorated_cb(x):
        return x * 2

    assert getRegisteredCallback("decorated") is my_decorated_cb
    assert triggerCallback("decorated", 5) == 10


def test_clear_callbacks():
    """Test that clearCallbacks removes all callbacks."""
    registerCallback("a", lambda: "a")
    registerCallback("b", lambda: "b")
    clearCallbacks()
    assert getRegisteredCallback("a") is None
    assert getRegisteredCallback("b") is None
