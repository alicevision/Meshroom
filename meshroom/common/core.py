from . import PySignal


class CoreDictModel:

    def __init__(self, keyAttrName, **kwargs):
        self._objects = {}
        self._keyAttrName = keyAttrName

    def __len__(self):
        return len(self._objects)

    def __bool__(self):
        return bool(self._objects)

    def __iter__(self):
        """ Enables iteration over the list of objects. """
        return iter(self._objects.values())

    def keys(self):
        return self._objects.keys()

    def items(self):
        return self._objects.items()

    def values(self):
        return self._objects.values()

    @property
    def objects(self):
        return self._objects

    def get(self, key):
        """
        :param key:
        :return: the value or None if not found
        """
        return self._objects.get(key)

    def getr(self, key):
        """
        Get or raise an error if the key does not exists.
        :param key:
        :return: the value
        """
        return self._objects[key]

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
        del self._objects[getattr(obj, self._keyAttrName)]

    def clear(self):
        self._objects.clear()

    def update(self, objects):
        for obj in objects:
            self.add(obj)

    def reset(self, objects):
        self.clear()
        self.update(objects)


class CoreListModel:
    def __init__(self, parent=None):
        self._objects = []

    def __iter__(self):
        return self._objects.__iter__()

    def __len__(self):
        return len(self._objects)

    def __getitem__(self, idx):
        return self._objects[idx]

    def values(self):
        return self._objects

    def setObjectList(self, iterable):
        self.clear()
        self._objects = iterable

    def at(self, idx):
        return self._objects[idx]

    def append(self, obj):
        self._objects.append(obj)

    def extend(self, iterable):
        self._objects.extend(iterable)

    def indexOf(self, obj):
        return self._objects.index(obj)

    def removeAt(self, idx, count=1):
        del self._objects[idx:idx+count]

    def remove(self, obj):
        self._objects.remove(obj)

    def clear(self):
        self._objects = []

    def insert(self, index, iterable):
        self._objects[index:index] = iterable


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

    def __init__(self, parent=None, *args, **kwargs):
        super(CoreObject, self).__init__()
        self._parent = parent
        # Note: we do not use ClassSignal, as it can not be used in __del__.
        self.destroyed = PySignal.Signal()

    def __del__(self):
        self.destroyed.emit()

    def parent(self):
        return self._parent


DictModel = CoreDictModel
ListModel = CoreListModel
Slot = CoreSlot
Signal = PySignal.ClassSignal
Property = CoreProperty
BaseObject = CoreObject
Variant = object
VariantList = object
JSValue = None
