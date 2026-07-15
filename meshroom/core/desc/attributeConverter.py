"""
attributeConverter: base descriptors class for AttributeConverter nodes
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from itertools import chain
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


class AttributeConverterRegistry:
    """
    Registry of available converters
    """

    _converters = defaultdict(list)  # { (srcType, dstType): [converters] }

    @classmethod
    def add(cls, converterClass):
        logging.info(
            f"Add converter class: {converterClass.__name__} "
            f"({converterClass.srcType.__name__} -> {converterClass.dstType.__name__})"
        )
        if not issubclass(converterClass, AttributeConverter):
            raise TypeError(f"{converterClass} must subclass AttributeConverter")
        cls._converters[(converterClass.srcType, converterClass.dstType)].append(converterClass)

    @classmethod
    def getAllConverters(cls) -> list[AttributeConverter]:
        return list(chain.from_iterable(cls._converters.values()))

    @classmethod
    def getConverters(cls, srcType, dstType) -> list[AttributeConverter]:
        """ Get priority-ordered converters.
        """
        converters = cls._converters.get((srcType, dstType))
        return sorted(converters, key=lambda c: -c.priority)

    @classmethod
    def getConverter(cls, srcType, dstType) -> AttributeConverter:
        """ Get highest priority converter. """
        converters = cls.getConverters(srcType, dstType)
        if not converters:
            return None
        return converters[0]
