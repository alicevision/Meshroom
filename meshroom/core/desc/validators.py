from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from meshroom.core.attribute import Attribute
    from meshroom.core.node import Node


def success() -> tuple[bool, list[str]]:
    return (True, [])

def error(*messages: str) -> tuple[bool, list[str]]:
    return (False, list(messages))

@runtime_checkable
class AttributeValidator(Protocol):
    """
    Interface for an attribute validation.
    This class can be inherited, and the __call__ methods overridden to implement any custom attribute validation logic.

    Because it is a callable class, validators can also be created on the fly.

    .. code-block: python
        lambda node, attribute: success() if attribute.value and attribute.value != "" else error("attribute have no value")
    """

    def __call__(self, node: "Node", attribute: "Attribute") -> tuple[bool, list[str]]:
        """
        This method can be overridden to implement any custom attribute validation logic.
        The `success()` and `error()` helpers can be used to encapsulate the returning responses.

        :param node: The node that holds the attribute to validate
        :param attribute: The attribute to validate

        :returns: The validation response: (True, []) if it is valid, (False, [errorMessage1, errorMessage2, ...]) otherwise.
        """
        raise NotImplementedError()


class NotEmptyValidator(AttributeValidator):
    """
    Ensure that the attribute value is not empty.
    This class is used to determine if an attribute value should be considered as mandatory/required.
    """

    def __call__(self, node: "Node", attribute: "Attribute") -> tuple[bool, list[str]]:
        if attribute.value is None or attribute.value == "":
            return error("An empty value is not allowed.")

        return success()


class RangeValidator(AttributeValidator):
    """ Check if the attribute value is in a given range. """

    def __init__(self, min, max):
        self._min = min
        self._max = max

    def __call__(self, node: "Node", attribute: "Attribute") -> tuple[bool, list[str]]:
        if attribute.value < self._min or attribute.value > self._max:
            return error(f"Value should be greater than {self._min} and less than {self._max} ",
                         f"({self._min} < {attribute.value} < {self._max}).")

        return success()