
class Attribute(object):
    """
    """
    isOutput = False
    uid = []
    group = 'allParams'
    commandLine = '{nodeType} --help'  # need to be overridden

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class FileAttribute(Attribute):
    """
    """
    def __init__(self, **kwargs):
        super(FileAttribute, self).__init__(**kwargs)


class ParamAttribute(Attribute):
    """
    """
    def __init__(self, **kwargs):
        super(ParamAttribute, self).__init__(**kwargs)


class Node(object):
    """
    """
    internalFolder = '{nodeType}/{uid0}/'

    def __init__(self):
        pass


class CommandLineNode(Node):
    """
    """
