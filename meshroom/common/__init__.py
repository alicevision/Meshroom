import meshroom

DictModel = None
ListModel = None
Slot = None
Signal = None
Property = None
BaseObject = None
Variant = None
VariantList = None
JSValue = None

if meshroom.backend == meshroom.Backend.PYSIDE:
    # PySide types
    from .qt import DictModel, ListModel, Slot, Signal, Property, BaseObject, Variant, VariantList, JSValue
elif meshroom.backend == meshroom.Backend.STANDALONE:
    # Core types
    from .core import DictModel, ListModel, Slot, Signal, Property, BaseObject, Variant, VariantList, JSValue


class _BaseModel:
    """ Common API for model implementation """

    def __init__(self, keyAttrName="name", **kwargs):
        """
        :param keyAttrName: name of the attribute containing the unique key for an object
        """
        pass

    @property
    def objects(self):
        """ Return a dictionary with {unique_key: object} mapping"""
        return None

    def get(self, key):
        """ Get the object with the unique key 'key' """
        pass

    def add(self, obj):
        """ Add given object using its 'keyAttrName' as unique key """
        pass

    def pop(self, key):
        """ Remove 'item' with unique key 'key' from the model """
        pass

    def remove(self, obj):
        """ Remove 'obj' from the model """
        pass

    def clear(self):
        """ Remove all internal objects """
        pass

    def update(self, d):
        """ Combine dict 'd' with self """
        pass

    def reset(self, d):
        """ Reset model with given values """
        pass
