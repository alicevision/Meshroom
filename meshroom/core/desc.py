from meshroom.common import BaseObject, Property, Variant


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
    

class ListAttribute(Attribute):
    """ A list of Attributes """
    def __init__(self, elementDesc, label, description, group='allParams'):
        """
        :param elementDesc: the Attribute description of elements to store in that list
        """
        self.elementDesc = elementDesc
        super(ListAttribute, self).__init__(label=label, description=description, value=None, uid=(), group=group)


class GroupAttribute(Attribute):
    """ A macro Attribute composed of several Attributes """
    def __init__(self, groupDesc, label, description, group='allParams'):
        """
        :param groupDesc: the description of the Attributes composing this group
        """
        self.groupDesc = groupDesc
        super(GroupAttribute, self).__init__(label=label, description=description, value=None, uid=(), group=group)


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


class BoolParam(Param):
    """
    """
    def __init__(self, label, description, value, uid, group='allParams'):
        super(BoolParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)


class IntParam(Param):
    """
    """
    def __init__(self, label, description, value, range, uid, group='allParams'):
        self._range = range
        super(IntParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)

    range = Property(Variant, lambda self: self._range, constant=True)


class FloatParam(Param):
    """
    """
    def __init__(self, label, description, value, range, uid, group='allParams'):
        self._range = range
        super(FloatParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)

    range = Property(Variant, lambda self: self._range, constant=True)


class ChoiceParam(Param):
    """
    """
    def __init__(self, label, description, value, values, exclusive, uid, group='allParams', joinChar=' '):
        self._values = values
        self._exclusive = exclusive
        self._joinChar = joinChar
        super(ChoiceParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)

    values = Property(Variant, lambda self: self._values, constant=True)
    exclusive = Property(bool, lambda self: self._exclusive, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)


class StringParam(Param):
    """
    """
    def __init__(self, label, description, value, uid, group='allParams'):
        super(StringParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)


class Node(object):
    """
    """
    internalFolder = '{nodeType}/{uid0}/'

    def __init__(self):
        pass


class CommandLineNode(Node):
    """
    """
