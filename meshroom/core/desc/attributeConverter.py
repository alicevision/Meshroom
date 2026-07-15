"""
attributeConverter: base descriptors class for AttributeConverter nodes
"""

from abc import ABC, abstractmethod
from .attribute import Attribute


class AttributeConverter(ABC):
    """
    Base class for converting the value of a source Attribute
    into a value for a destination Attribute of a different type, 
    so a connection can be made between them.
    """
    
    # Put a higher number to prioritize specific converters
    priority = 10

    # Input / Output classes
    srcType: Attribute = None
    dstType: Attribute = None

    @classmethod
    def canConvert(cls, srcType, dstType):
        """ Check if this converter corresponds to a source/destination attribute pair.
        """
        return isinstance(srcType, cls.srcType) and isinstance(dstType, cls.dstType)

    @classmethod
    @abstractmethod
    def convert(cls, value):
        """ Convert a value from the source attribute's type to a value for
        the destination attribute's type.
        """
        return value

    @classmethod
    def isValid(cls, value):
        """ In general case we suppose the conversion is always possible, but
        this method enables optional type checking.
        """
        return True

    def __repr__(self):
        return f"<AttributeConverter '{self.__class__.__name__}': {self.srcType} -> {self.dstType}>"
