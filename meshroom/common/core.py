
class CoreModel:

    def __init__(self, keyAttrName="name", **kwargs):
        self._objects = {}
        self._keyAttrName = keyAttrName

    def __len__(self):
        return len(self._objects)

    def __iter__(self):
        """ Enables iteration over the list of objects. """
        return iter(self._objects.values())

    @property
    def objects(self):
        return self._objects

    def get(self, key):
        return self._objects.get(key, None)

    def add(self, obj):
        key = getattr(obj, self._keyAttrName, None)
        assert key is not None
        assert key not in self._objects
        self._objects[key] = obj

    def pop(self, key):
        assert key in self._objects
        return self._objects.pop(key)

    def remove(self, obj):
        assert obj in self._objects.values()
        return self._objects.pop(getattr(obj, self._keyAttrName))

    def clear(self):
        self._objects = {}


class CoreSignal:
    """ Fake signal that doesn't do anything """
    def emit(self):
        pass


def CoreSlot(*args, **kwargs):
    def slot_decorator(func):
        def func_wrapper(*f_args, **f_kwargs):
            return func(*f_args, **f_kwargs)
        return func_wrapper
    return slot_decorator


class CoreProperty(property):
    def __init__(self, ptype, fget=None, fset=None, **kwargs):
        super(CoreProperty, self).__init__(fget, fset)


class CoreObject(object):
    def __init__(self, *args, **kwargs):
        super(CoreObject, self).__init__()


Model = CoreModel
Slot = CoreSlot
Signal = CoreSignal
Property = CoreProperty
BaseObject = CoreObject
