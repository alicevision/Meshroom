
class Attribute(object):
    """
    """
    isOutput = False
    uid = []
    group = 'allParams'
    commandLine = '{nodeType} --help'  # need to be overridden

    def __init__(self, label, description, value, uid, group):
        self.label = label
        self.description = description
        self.value = value
        self.uid = uid
        self.group = group


class Param(Attribute):
    """
    """
    def __init__(self, label, description, value, uid, group):
        super(Param, self).__init__(label=label, description=description, value=value, uid=uid, group=group)


class File(Attribute):
    """
    """
    def __init__(self, label, description, value, uid, isOutput, group='allParams'):
        self.isOutput = isOutput
        super(File, self).__init__(label=label, description=description, value=value, uid=uid, group=group)


class BoolParam(Param):
    """
    """
    def __init__(self, label, description, value, uid, group='allParams'):
        super(BoolParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)


class IntParam(Param):
    """
    """
    def __init__(self, label, description, value, range, uid, group='allParams'):
        self.range = range
        super(IntParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)


class FloatParam(Param):
    """
    """
    def __init__(self, label, description, value, range, uid, group='allParams'):
        self.range = range
        super(FloatParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)


class ChoiceParam(Param):
    """
    """
    def __init__(self, label, description, value, values, exclusive, uid, group='allParams', joinChar=' '):
        self.values = values
        self.exclusive = exclusive
        self.joinChar = joinChar
        super(ChoiceParam, self).__init__(label=label, description=description, value=value, uid=uid, group=group)


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
