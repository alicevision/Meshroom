from meshroom.common import BaseObject, Property, Variant
from enum import Enum  # available by default in python3. For python2: "pip install enum34"
import collections
import math
import os
import psutil

class Attribute(BaseObject):
    """
    """

    def __init__(self, name, label, description, value, uid, group):
        super(Attribute, self).__init__()
        self._name = name
        self._label = label
        self._description = description
        self._value = value
        self._uid = uid
        self._group = group
        # self._isOutput = False

    name = Property(str, lambda self: self._name, constant=True)
    label = Property(str, lambda self: self._label, constant=True)
    description = Property(str, lambda self: self._description, constant=True)
    value = Property(Variant, lambda self: self._value, constant=True)
    uid = Property(Variant, lambda self: self._uid, constant=True)
    group = Property(str, lambda self: self._group, constant=True)
    # isOutput = Property(bool, lambda self: self._isOutput, constant=True)
    # isInput = Property(bool, lambda self: not self._isOutput, constant=True)

    def validateValue(self, value):
        return value


class ListAttribute(Attribute):
    """ A list of Attributes """
    def __init__(self, elementDesc, name, label, description, group='allParams'):
        """
        :param elementDesc: the Attribute description of elements to store in that list
        """
        self.elementDesc = elementDesc
        super(ListAttribute, self).__init__(name=name, label=label, description=description, value=None, uid=(), group=group)

    uid = Property(Variant, lambda self: self.elementDesc.uid, constant=True)

    def validateValue(self, value):
        if not (isinstance(value, collections.Iterable) and isinstance(value, basestring)):
            raise ValueError('ListAttribute only supports iterable input values.')
        return value


class GroupAttribute(Attribute):
    """ A macro Attribute composed of several Attributes """
    def __init__(self, groupDesc, name, label, description, group='allParams'):
        """
        :param groupDesc: the description of the Attributes composing this group
        """
        self.groupDesc = groupDesc
        super(GroupAttribute, self).__init__(name=name, label=label, description=description, value=None, uid=(), group=group)

    def validateValue(self, value):
        if not (isinstance(value, collections.Iterable) and isinstance(value, basestring)):
            raise ValueError('GroupAttribute only supports iterable input values.')
        return value

    def retrieveChildrenUids(self):
        allUids = []
        for desc in self.groupDesc:
            allUids.extend(desc.uid)
        return allUids

    uid = Property(Variant, retrieveChildrenUids, constant=True)


class Param(Attribute):
    """
    """
    def __init__(self, name, label, description, value, uid, group):
        super(Param, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group)


class File(Attribute):
    """
    """
    def __init__(self, name, label, description, value, uid, group='allParams'):
        super(File, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        if not isinstance(value, basestring):
            raise ValueError('File only supports string input: "{}".'.format(value))
        return os.path.normpath(value).replace('\\', '/')


class BoolParam(Param):
    """
    """
    def __init__(self, name, label, description, value, uid, group='allParams'):
        super(BoolParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        try:
            return bool(value)
        except:
            raise ValueError('BoolParam only supports bool value.')


class IntParam(Param):
    """
    """
    def __init__(self, name, label, description, value, range, uid, group='allParams'):
        self._range = range
        super(IntParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        try:
            return int(value)
        except:
            raise ValueError('IntParam only supports int value.')

    range = Property(Variant, lambda self: self._range, constant=True)


class FloatParam(Param):
    """
    """
    def __init__(self, name, label, description, value, range, uid, group='allParams'):
        self._range = range
        super(FloatParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        try:
            return float(value)
        except:
            raise ValueError('FloatParam only supports float value.')

    range = Property(Variant, lambda self: self._range, constant=True)


class ChoiceParam(Param):
    """
    """
    def __init__(self, name, label, description, value, values, exclusive, uid, group='allParams', joinChar=' '):
        self._values = values
        self._exclusive = exclusive
        self._joinChar = joinChar
        super(ChoiceParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group)

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
    def __init__(self, name, label, description, value, uid, group='allParams'):
        super(StringParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group)

    def validateValue(self, value):
        if not isinstance(value, basestring):
            raise ValueError('StringParam value "{}" should be a string.'.format(value))
        return value


class Level(Enum):
    NONE = 0
    NORMAL = 1
    INTENSIVE = 2


class Range:
    def __init__(self, iteration=0, blockSize=0, fullSize=0):
        self.iteration = iteration
        self.blockSize = blockSize
        self.fullSize = fullSize

    @property
    def start(self):
        return self.iteration * self.blockSize

    @property
    def effectiveBlockSize(self):
        remaining = (self.fullSize - self.start) + 1
        return self.blockSize if remaining >= self.blockSize else remaining

    @property
    def end(self):
        return self.start + self.effectiveBlockSize

    @property
    def last(self):
        return self.end - 1

    def toDict(self):
        return {
            "rangeIteration": self.iteration,
            "rangeStart": self.start,
            "rangeEnd": self.end,
            "rangeLast": self.last,
            "rangeBlockSize": self.effectiveBlockSize,
            "rangeFullSize": self.fullSize,
            }


class Parallelization:
    def __init__(self, inputListParamName='', staticNbBlocks=0, blockSize=0):
        self.inputListParamName = inputListParamName
        self.staticNbBlocks = staticNbBlocks
        self.blockSize = blockSize

    def getSizes(self, node):
        """
        Args:
            node:
        Returns: (blockSize, fullSize, nbBlocks)
        """
        if self.inputListParamName:
            parentNodes, edges = node.graph.dfsOnFinish(startNodes=[node])
            for parentNode in parentNodes:
                if self.inputListParamName in parentNode.getAttributes().keys():
                    fullSize = len(parentNode.attribute(self.inputListParamName))
                    nbBlocks = int(math.ceil(float(fullSize) / float(self.blockSize)))
                    return (self.blockSize, fullSize, nbBlocks)
            raise RuntimeError('Cannot find the "inputListParamName": "{}" in the list of input nodes: {} for node: {}'.format(self.inputListParamName, parentNodes, node.name))
        if self.staticNbBlocks:
            return (1, self.staticNbBlocks, self.staticNbBlocks)
        return None

    def getRange(self, node, iteration):
        blockSize, fullSize, nbBlocks = self.getSizes(node)
        return Range(iteration=iteration, blockSize=blockSize, fullSize=fullSize)

    def getRanges(self, node):
        blockSize, fullSize, nbBlocks = self.getSizes(node)
        ranges = []
        for i in range(nbBlocks):
            ranges.append(Range(iteration=i, blockSize=blockSize, fullSize=fullSize))
        return ranges


class Node(object):
    """
    """
    internalFolder = '{nodeType}/{uid0}/'
    cpu = Level.NORMAL
    gpu = Level.NONE
    ram = Level.NORMAL
    packageName = ''
    packageVersion = ''
    inputs = []
    outputs = []
    parallelization = None

    def __init__(self):
        pass

    def updateInternals(self, node):
        pass

    def stop(self, node):
        pass

    def processChunk(self, node, range):
        raise NotImplementedError('No process implementation on node: "{}"'.format(node.name))


class CommandLineNode(Node):
    """
    """
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = ''  # need to be defined on the node
    parallelization = None
    commandLineRange = ''

    def buildCommandLine(self, chunk):
        cmdPrefix = ''
        if 'REZ_ENV' in os.environ:
            cmdPrefix = '{rez} {packageFullName} -- '.format(rez=os.environ.get('REZ_ENV'), packageFullName=chunk.node.packageFullName)
        cmdSuffix = ''
        if chunk.range:
            cmdSuffix = ' ' + self.commandLineRange.format(**chunk.range.toDict())
        return cmdPrefix + chunk.node.nodeDesc.commandLine.format(**chunk.node._cmdVars) + cmdSuffix

    def stop(self, node):
        if node.subprocess:
            node.subprocess.terminate()

    def processChunk(self, chunk):
        try:
            with open(chunk.logFile(), 'w') as logF:
                cmd = self.buildCommandLine(chunk)
                print(' - commandLine:', cmd)
                print(' - logFile:', chunk.logFile())
                chunk.subprocess = psutil.Popen(cmd, stdout=logF, stderr=logF, shell=True)

                # store process static info into the status file
                chunk.status.commandLine = cmd
                # chunk.status.env = node.proc.environ()
                # chunk.status.createTime = node.proc.create_time()

                chunk.statThread.proc = chunk.subprocess
                stdout, stderr = chunk.subprocess.communicate()
                chunk.subprocess.wait()

                chunk.status.returnCode = chunk.subprocess.returncode

            if chunk.subprocess.returncode != 0:
                with open(chunk.logFile(), 'r') as logF:
                    logContent = ''.join(logF.readlines())
                raise RuntimeError('Error on node "{}":\nLog:\n{}'.format(chunk.name, logContent))
        except:
            raise
        finally:
            chunk.subprocess = None

