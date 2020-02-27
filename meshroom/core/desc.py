from meshroom.common import BaseObject, Property, Variant, VariantList
from meshroom.core import pyCompatibility
from enum import Enum  # available by default in python3. For python2: "pip install enum34"
import collections
import math
import os
import psutil


class Attribute(BaseObject):
    """
    """

    def __init__(self, name, label, description, value, advanced, uid, group):
        super(Attribute, self).__init__()
        self._name = name
        self._label = label
        self._description = description
        self._value = value
        self._uid = uid
        self._group = group
        self._advanced = advanced

    name = Property(str, lambda self: self._name, constant=True)
    label = Property(str, lambda self: self._label, constant=True)
    description = Property(str, lambda self: self._description, constant=True)
    value = Property(Variant, lambda self: self._value, constant=True)
    uid = Property(Variant, lambda self: self._uid, constant=True)
    group = Property(str, lambda self: self._group, constant=True)
    advanced = Property(bool, lambda self: self._advanced, constant=True)
    type = Property(str, lambda self: self.__class__.__name__, constant=True)

    def validateValue(self, value):
        """ Return validated/conformed 'value'.

        Raises:
            ValueError: if value does not have the proper type
        """
        return value

    def matchDescription(self, value, conform=False):
        """ Returns whether the value perfectly match attribute's description.

        Args:
            value: the value
            conform: try to adapt value to match the description
        """
        try:
            self.validateValue(value)
        except ValueError:
            return False
        return True


class ListAttribute(Attribute):
    """ A list of Attributes """
    def __init__(self, elementDesc, name, label, description, group='allParams', advanced=False, joinChar=' '):
        """
        :param elementDesc: the Attribute description of elements to store in that list
        """
        self._elementDesc = elementDesc
        self._joinChar = joinChar
        super(ListAttribute, self).__init__(name=name, label=label, description=description, value=[], uid=(), group=group, advanced=advanced)

    elementDesc = Property(Attribute, lambda self: self._elementDesc, constant=True)
    uid = Property(Variant, lambda self: self.elementDesc.uid, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)

    def validateValue(self, value):
        if not isinstance(value, (list, tuple)):
            raise ValueError('ListAttribute only supports list/tuple input values (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))
        return value

    def matchDescription(self, value, conform=False):
        """ Check that 'value' content matches ListAttribute's element description. """
        if not super(ListAttribute, self).matchDescription(value, conform):
            return False
        # list must be homogeneous: only test first element
        if value:
            return self._elementDesc.matchDescription(value[0], conform)
        return True


class GroupAttribute(Attribute):
    """ A macro Attribute composed of several Attributes """
    def __init__(self, groupDesc, name, label, description, group='allParams', advanced=False, joinChar=' '):
        """
        :param groupDesc: the description of the Attributes composing this group
        """
        self._groupDesc = groupDesc
        self._joinChar = joinChar
        super(GroupAttribute, self).__init__(name=name, label=label, description=description, value={}, uid=(), group=group, advanced=advanced)

    groupDesc = Property(Variant, lambda self: self._groupDesc, constant=True)

    def validateValue(self, value):
        """ Ensure value is a dictionary with keys compatible with the group description. """
        if not isinstance(value, dict):
            raise ValueError('GroupAttribute only supports dict input values (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))
        invalidKeys = set(value.keys()).difference([attr.name for attr in self._groupDesc])
        if invalidKeys:
            raise ValueError('Value contains key that does not match group description : {}'.format(invalidKeys))
        return value

    def matchDescription(self, value, conform=False):
        """
        Check that 'value' contains the exact same set of keys as GroupAttribute's group description
        and that every child value match corresponding child attribute description.

        Args:
            value: the value
            conform: remove entries that don't exist in the description.
        """
        if not super(GroupAttribute, self).matchDescription(value):
            return False
        attrMap = {attr.name: attr for attr in self._groupDesc}

        if conform:
            # remove invalid keys
            invalidKeys = set(value.keys()).difference([attr.name for attr in self._groupDesc])
            for k in invalidKeys:
                del self._groupDesc[k]
        else:
            # must have the exact same child attributes
            if sorted(value.keys()) != sorted(attrMap.keys()):
                return False

        for k, v in value.items():
            # each child value must match corresponding child attribute description
            if not attrMap[k].matchDescription(v, conform):
                return False
        return True

    def retrieveChildrenUids(self):
        allUids = []
        for desc in self._groupDesc:
            allUids.extend(desc.uid)
        return allUids

    uid = Property(Variant, retrieveChildrenUids, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)


class Param(Attribute):
    """
    """
    def __init__(self, name, label, description, value, uid, group, advanced):
        super(Param, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced)


class File(Attribute):
    """
    """
    def __init__(self, name, label, description, value, uid, group='allParams', advanced=False):
        super(File, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced)

    def validateValue(self, value):
        if not isinstance(value, pyCompatibility.basestring):
            raise ValueError('File only supports string input  (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))
        return os.path.normpath(value).replace('\\', '/') if value else ''


class BoolParam(Param):
    """
    """
    def __init__(self, name, label, description, value, uid, group='allParams', advanced=False):
        super(BoolParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced)

    def validateValue(self, value):
        try:
            return bool(int(value)) # int cast is useful to handle string values ('0', '1')
        except:
            raise ValueError('BoolParam only supports bool value (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))


class IntParam(Param):
    """
    """
    def __init__(self, name, label, description, value, range, uid, group='allParams', advanced=False):
        self._range = range
        super(IntParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced)

    def validateValue(self, value):
        # handle unsigned int values that are translated to int by shiboken and may overflow
        try:
            return long(value)  # Python 2
        except NameError:
            return int(value)   # Python 3
        except:
            raise ValueError('IntParam only supports int value (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))

    range = Property(VariantList, lambda self: self._range, constant=True)


class FloatParam(Param):
    """
    """
    def __init__(self, name, label, description, value, range, uid, group='allParams', advanced=False):
        self._range = range
        super(FloatParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced)

    def validateValue(self, value):
        try:
            return float(value)
        except:
            raise ValueError('FloatParam only supports float value (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))

    range = Property(VariantList, lambda self: self._range, constant=True)


class ChoiceParam(Param):
    """
    """
    def __init__(self, name, label, description, value, values, exclusive, uid, group='allParams', joinChar=' ', advanced=False):
        assert values
        self._values = values
        self._exclusive = exclusive
        self._joinChar = joinChar
        self._valueType = type(self._values[0])  # cast to value type
        super(ChoiceParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced)

    def conformValue(self, val):
        """ Conform 'val' to the correct type and check for its validity """
        val = self._valueType(val)
        if val not in self.values:
            raise ValueError('ChoiceParam value "{}" is not in "{}".'.format(val, str(self.values)))
        return val

    def validateValue(self, value):
        if self.exclusive:
            return self.conformValue(value)

        if not isinstance(value, collections.Iterable):
            raise ValueError('Non exclusive ChoiceParam value should be iterable (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))
        return [self.conformValue(v) for v in value]

    values = Property(VariantList, lambda self: self._values, constant=True)
    exclusive = Property(bool, lambda self: self._exclusive, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)


class StringParam(Param):
    """
    """
    def __init__(self, name, label, description, value, uid, group='allParams', advanced=False):
        super(StringParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced)

    def validateValue(self, value):
        if not isinstance(value, pyCompatibility.basestring):
            raise ValueError('StringParam value should be a string (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))
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
            "rangeBlockSize": self.blockSize,
            "rangeEffectiveBlockSize": self.effectiveBlockSize,
            "rangeFullSize": self.fullSize,
            }


class Parallelization:
    def __init__(self, staticNbBlocks=0, blockSize=0):
        self.staticNbBlocks = staticNbBlocks
        self.blockSize = blockSize

    def getSizes(self, node):
        """
        Args:
            node:
        Returns: (blockSize, fullSize, nbBlocks)
        """
        size = node.size
        if self.blockSize:
            nbBlocks = int(math.ceil(float(size) / float(self.blockSize)))
            return self.blockSize, size, nbBlocks
        if self.staticNbBlocks:
            return 1, self.staticNbBlocks, self.staticNbBlocks
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


class DynamicNodeSize(object):
    """
    DynamicNodeSize expresses a dependency to an input attribute to define
    the size of a Node in terms of individual tasks for parallelization.
    If the attribute is a link to another node, Node's size will be the same as this connected node.
    If the attribute is a ListAttribute, Node's size will be the size of this list.
    """
    def __init__(self, param):
        self._param = param

    def computeSize(self, node):
        param = node.attribute(self._param)
        # Link: use linked node's size
        if param.isLink:
            return param.getLinkParam().node.size
        # ListAttribute: use list size
        if isinstance(param.desc, ListAttribute):
            return len(param)
        if isinstance(param.desc, IntParam):
            return param.value
        return 1


class MultiDynamicNodeSize(object):
    """
    MultiDynamicNodeSize expresses dependencies to multiple input attributes to
    define the size of a node in terms of individual tasks for parallelization.
    Works as DynamicNodeSize and sum the sizes of each dependency.
    """
    def __init__(self, params):
        """
        Args:
            params (list): list of input attributes names
        """
        assert isinstance(params, (list, tuple))
        self._params = params

    def computeSize(self, node):
        size = 0
        for param in self._params:
            param = node.attribute(param)
            if param.isLink:
                size += param.getLinkParam().node.size
            elif isinstance(param.desc, ListAttribute):
                size += len(param)
            else:
                size += 1
        return size


class StaticNodeSize(object):
    """
    StaticNodeSize expresses a static Node size in terms of individual tasks for parallelization.
    """
    def __init__(self, size):
        self._size = size

    def computeSize(self, node):
        return self._size


class Node(object):
    """
    """
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    cpu = Level.NORMAL
    gpu = Level.NONE
    ram = Level.NORMAL
    packageName = ''
    packageVersion = ''
    inputs = []
    outputs = []
    size = StaticNodeSize(1)
    parallelization = None

    def __init__(self):
        pass

    @classmethod
    def update(cls, node):
        """ Method call before node's internal update on invalidation.

        Args:
            node: the BaseNode instance being updated
        See Also:
            BaseNode.updateInternals
        """
        pass

    @classmethod
    def postUpdate(cls, node):
        """ Method call after node's internal update on invalidation.

        Args:
            node: the BaseNode instance being updated
        See Also:
            NodeBase.updateInternals
        """
        pass

    def stopProcess(self, chunk):
        raise NotImplementedError('No stopProcess implementation on node: {}'.format(chunk.node.name))

    def processChunk(self, chunk):
        raise NotImplementedError('No processChunk implementation on node: "{}"'.format(chunk.node.name))


class CommandLineNode(Node):
    """
    """
    commandLine = ''  # need to be defined on the node
    parallelization = None
    commandLineRange = ''

    def buildCommandLine(self, chunk):
        cmdPrefix = ''
        # if rez available in env, we use it
        if 'REZ_ENV' in os.environ and chunk.node.packageVersion:
            # if the node package is already in the environment, we don't need a new dedicated rez environment
            alreadyInEnv = os.environ.get('REZ_{}_VERSION'.format(chunk.node.packageName.upper()), "").startswith(chunk.node.packageVersion)
            if not alreadyInEnv:
                cmdPrefix = '{rez} {packageFullName} -- '.format(rez=os.environ.get('REZ_ENV'), packageFullName=chunk.node.packageFullName)
        cmdSuffix = ''
        if chunk.node.isParallelized:
            cmdSuffix = ' ' + self.commandLineRange.format(**chunk.range.toDict())
        return cmdPrefix + chunk.node.nodeDesc.commandLine.format(**chunk.node._cmdVars) + cmdSuffix

    def stopProcess(self, chunk):
        # the same node could exists several times in the graph and
        # only one would have the running subprocess; ignore all others
        if not hasattr(chunk, "subprocess"):
            return
        if chunk.subprocess:
            # kill process tree
            processes = chunk.subprocess.children(recursive=True) + [chunk.subprocess]
            try:
                for process in processes:
                    process.terminate()
            except psutil.NoSuchProcess:
                pass

    def processChunk(self, chunk):
        try:
            with open(chunk.logFile, 'w') as logF:
                cmd = self.buildCommandLine(chunk)
                chunk.status.commandLine = cmd
                chunk.saveStatusFile()
                print(' - commandLine: {}'.format(cmd))
                print(' - logFile: {}'.format(chunk.logFile))
                chunk.subprocess = psutil.Popen(cmd, stdout=logF, stderr=logF, shell=True)

                # store process static info into the status file
                # chunk.status.env = node.proc.environ()
                # chunk.status.createTime = node.proc.create_time()

                chunk.statThread.proc = chunk.subprocess
                stdout, stderr = chunk.subprocess.communicate()
                chunk.subprocess.wait()

                chunk.status.returnCode = chunk.subprocess.returncode

            if chunk.subprocess.returncode != 0:
                with open(chunk.logFile, 'r') as logF:
                    logContent = ''.join(logF.readlines())
                raise RuntimeError('Error on node "{}":\nLog:\n{}'.format(chunk.name, logContent))
        except:
            raise
        finally:
            chunk.subprocess = None

