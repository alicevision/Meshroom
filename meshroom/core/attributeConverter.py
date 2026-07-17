"""
attributeConverter: base descriptors class for AttributeConverter nodes
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar
from collections import defaultdict
from itertools import chain

if TYPE_CHECKING:
    from meshroom.core.desc.attribute import Attribute


class AttributeConverter(ABC):
    """
    Base class for converting the value of a source Attribute
    into a value for a destination Attribute of a different type, 
    so a connection can be made between them.
    """

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    priority: ClassVar[int] = 10  # Put a higher number to prioritize specific converters

    # Input / Output classes
    srcType: ClassVar["Attribute"] = None
    dstType: ClassVar["Attribute"] = None
    
    def __init__(self):
        if not all ((self.srcType, self.dstType)):
            raise TypeError(
                f"Class '{self.__class__.__name__}' must define srcType and dstType."
            )

    @classmethod
    def getName(cls):
        return cls.name or cls.__name__

    def canConvert(self, srcType, dstType):
        """ Check if this converter corresponds to a source/destination attribute pair.
        """
        return isinstance(srcType, self.srcType) and isinstance(dstType, self.dstType)

    @abstractmethod
    def convert(self, value):
        """ Convert a value from the source attribute's type to a value for
        the destination attribute's type.
        """
        return value

    def __repr__(self):
        return f"<AttributeConverter {self.getName()} ({self.srcType.__name__} -> {self.dstType.__name__})>"


class AttributeConverterRegistry:
    """
    Registry of available converters
    """

    # { (srcType, dstType): [converters] }
    _converters: dict[tuple["Attribute", "Attribute"], list[AttributeConverter]] = defaultdict(list)

    @classmethod
    def add(cls, converter: AttributeConverter):
        if not issubclass(converter.__class__, AttributeConverter):
            raise TypeError(f"{converter} parent class must subclass AttributeConverter")
        logging.info(
            f"Add converter class: {converter.getName()} "
            f"({converter.srcType.__name__} -> {converter.dstType.__name__})"
        )
        cls._converters[(converter.srcType.__name__, converter.dstType.__name__)].append(converter)

    @classmethod
    def getAllConverters(cls) -> list[AttributeConverter]:
        return list(chain.from_iterable(cls._converters.values()))

    @classmethod
    def getConverterByName(cls, name):
        for c in cls.getAllConverters():
            if c.getName() == name:
                return c
        return None

    @classmethod
    def hasConverter(cls, srcType: "Attribute", dstType: "Attribute") -> list[AttributeConverter]:
        return  ((srcType, dstType)) in cls._converters

    @classmethod
    def getConverters(cls, srcType: "Attribute", dstType: "Attribute") -> list[AttributeConverter]:
        """ Get priority-ordered converters.
        """
        converters = cls._converters.get((srcType, dstType), [])
        return sorted(converters, key=lambda c: -c.priority)

    @classmethod
    def getConverter(cls, srcType: "Attribute", dstType: "Attribute") -> AttributeConverter:
        """ Get highest priority converter. """
        converters = cls.getConverters(srcType, dstType)
        if not converters:
            return None
        return converters[0]
