from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from meshroom.core.attribute import Attribute
    from meshroom.core.node import Node


def success() -> tuple[bool, list[str]]:
    return (True, [])

def error(*messages: str) -> tuple[bool, list[str]]:
    return (False, messages)

class AttributeValidator(object):
    """ Interface for an attribute validation
        You can inherit from this class and override the __call__ methods to implement your own attribute validation logic

        Because it's a callable class, you can also create your own validators on the fly

        .. code-block: python

            lambda node, attribute: success() if attribute.value and attribute.value != "" else error("attribute have no value")
    """

    def __call__(self, node: "Node", attribute: "Attribute") -> tuple[bool, list[str]]:
        """
            Override this method to implement your custom validation logic.
            You can use the success() and error() helpers that encapsulate the returning response.

            :param node: The node that holds the attribute to validate
            :param attribute: The atribute to validate

            :returns: The validtion response: (True, []) if it's valid, (False, [errorMessage1, errorMessage2, ...]) if error exists

        """
        raise NotImplementedError()


class NotEmptyValidator(AttributeValidator):
    """ The attribute value should not be empty
        This class is used to determine if an attribute label should be considered as mandatory/required
    """

    def __call__(self, node: "Node", attribute: "Attribute") -> tuple[bool, list[str]]:

        if attribute.value is None or attribute.value == "":
            return error("Empty value are not allowed")
        
        return success()


class RangeValidator(AttributeValidator):
    """ Check if the attribute value is in the given range
    """

    def __init__(self, min, max):
        self._min = min
        self._max = max

    def __call__(self, node:"Node", attribute: "Attribute") -> tuple[bool, list[str]]:

        if attribute.value < self._min or attribute.value > self._max:
            return error(f"Value should be greater than {self._min} and less than {self._max}", 
                            f"({self._min} < {attribute.value} < {self._max})")

        return success()