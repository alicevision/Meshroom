from meshroom.common import BaseObject, Property, Variant
from enum import Enum  # available by default in python3. For python2: "pip install enum34"
import collections
import os


class Attribute(BaseObject):
    """
    """

    def __init__(self, label, description, value, uid, group):
        super(Attribute, self).__init__()
        self._label = label
        self._description = description
        self._value = value
        self._uid = uid
        self._group = group
        self._isOutput = False
    
    label = Property(str, lambda self: self._label, constant=True)
    description = Property(str, lambda self: self._description, constant=True)
    value = Property(Variant, lambda self: self._value, constant=True)
    uid = Property(Variant, lambda self: self._uid, constant=True)
    group = Property(str, lambda self: self._group, constant=True)
    isOutput = Property(bool, lambda self: self._isOutput, constant=True)
    isInput = Property(bool, lambda self: not self._isOutput, constant=True)

    def validateValue(self, value):
        return value


class ListAttribute(Attribute):
    """ A list of Attributes """
    def __init__(self, elementDesc, label, description, group='allParams'):
        """
        :param elementDesc: the Attribute description of elements to store in that list
        """
        self.elementDesc = elementDesc
        super(ListAttribute, self).__init__(label=label, description=description, value=None, uid=(), group=group)

    uid = Property(Variant, lambda self: self.elementDesc.uid, constant=True)

    def validateValue(self, value):
        if not (isinstance(value, collections.Iterable) and isinstance(value, basestring)):
            raise ValueError('ListAttribute only supports iterable input values.')
        return value


class GroupAttribute(Attribute):
    """ A macro Attribute composed of several Attributes """
    def __init__(self, groupDesc, label, description, group='allParams'):
        """
        :param groupDesc: the description of the Attributes composing this group
        """
        self.groupDesc = groupDesc
        super(GroupAttribute, self).__init__(label=label, description=description, value=None, uid=(), group=group)

    def validateValue(self, value):
        if not (isinstance(value, collections.Iterable) and isinstance(value, basestring)):
            raise ValueError('GroupAttribute only supports iterable input values.')
        return value

    def retrieveChildrenUids(self):
        allUids = []
        for desc in self.groupDesc.values():
            allUids.extend(desc.uid)
        return allUids

    uid = Property(Variant, retrieveChildrenUids, constant=True)


class Param(Attribute):
    """
    """
    def __init__(self, label, description, value, uid, group):
        super(Param, self).__init__(label=label, description=description, value=value, uid=uid, group=group)


class File(Attribute):
    """
    """
    def __init__(self, label, description, value, uid, isOutput, group='allParams'):
        super(File, self).__init__(label=label, description=description, value=value, uid=uid, group=group)
        self._isOutput = isOutput

    def validateValue(self, value):
        if not isinstance(value, basestring):
            raise ValueError('File only supports string input: "{}".'.format(value))
        return os.path.normpath(value).replace('\\', '/')


class BoolParam(Param):
    """
    """
    def __init__(self, label, description, value, uid, group='allParams'):
        super(BoolParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        try:
            return bool(value)
        except:
            raise ValueError('BoolParam only supports bool value.')


class IntParam(Param):
    """
    """
    def __init__(self, label, description, value, range, uid, group='allParams'):
        self._range = range
        super(IntParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        try:
            return int(value)
        except:
            raise ValueError('IntParam only supports int value.')

    range = Property(Variant, lambda self: self._range, constant=True)


class FloatParam(Param):
    """
    """
    def __init__(self, label, description, value, range, uid, group='allParams'):
        self._range = range
        super(FloatParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        try:
            return float(value)
        except:
            raise ValueError('FloatParam only supports float value.')

    range = Property(Variant, lambda self: self._range, constant=True)


class ChoiceParam(Param):
    """
    """
    def __init__(self, label, description, value, values, exclusive, uid, group='allParams', joinChar=' '):
        self._values = values
        self._exclusive = exclusive
        self._joinChar = joinChar
        super(ChoiceParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        newValues = None
        if self.exclusive:
            newValues = [value]
        else:
            if not isinstance(value, collections.Iterable):
                raise ValueError('Non exclusive ChoiceParam value "{}" should be iterable.'.format(value))
            newValues = value
        for newValue in newValues:
            if newValue not in self.values:
                raise ValueError('ChoiceParam value "{}" is not in "{}".'.format(newValue, str(self.values)))
        return value

    values = Property(Variant, lambda self: self._values, constant=True)
    exclusive = Property(bool, lambda self: self._exclusive, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)


class StringParam(Param):
    """
    """
    def __init__(self, label, description, value, uid, group='allParams'):
        super(StringParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        if not isinstance(value, basestring):
            raise ValueError('StringParam value "{}" should be a string.'.format(value))
        return value


class Level(Enum):
    NONE = 0
    NORMAL = 1
    INTENSIVE = 2


class Node(object):
    """
    """
    internalFolder = '{nodeType}/{uid0}/'
    cpu = Level.NORMAL
    gpu = Level.NONE
    ram = Level.NORMAL
    packageName = ''
    packageVersion = ''

    def __init__(self):
        pass


class CommandLineNode(Node):
    """
    """
