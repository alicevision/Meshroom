from meshroom.common import BaseObject, Property, Variant, VariantList, JSValue
from meshroom.core import pyCompatibility
from enum import Enum  # available by default in python3. For python2: "pip install enum34"
import math
import os
import psutil
import ast

class Attribute(BaseObject):
    """
    """

    def __init__(self, name, label, description, value, advanced, semantic, uid, group, enabled):
        super(Attribute, self).__init__()
        self._name = name
        self._label = label
        self._description = description
        self._value = value
        self._uid = uid
        self._group = group
        self._advanced = advanced
        self._enabled = enabled
        self._semantic = semantic

    name = Property(str, lambda self: self._name, constant=True)
    label = Property(str, lambda self: self._label, constant=True)
    description = Property(str, lambda self: self._description, constant=True)
    value = Property(Variant, lambda self: self._value, constant=True)
    uid = Property(Variant, lambda self: self._uid, constant=True)
    group = Property(str, lambda self: self._group, constant=True)
    advanced = Property(bool, lambda self: self._advanced, constant=True)
    enabled = Property(Variant, lambda self: self._enabled, constant=True)
    semantic = Property(str, lambda self: self._semantic, constant=True)
    type = Property(str, lambda self: self.__class__.__name__, constant=True)

    def validateValue(self, value):
        """ Return validated/conformed 'value'. Need to be implemented in derived classes.

        Raises:
            ValueError: if value does not have the proper type
        """
        raise NotImplementedError("Attribute.validateValue is an abstract function that should be implemented in the derived class.")

    def matchDescription(self, value, strict=True):
        """ Returns whether the value perfectly match attribute's description.

        Args:
            value: the value
            strict: strict test for the match (for instance, regarding a group with some parameter changes)
        """
        try:
            self.validateValue(value)
        except ValueError:
            return False
        return True


class ListAttribute(Attribute):
    """ A list of Attributes """
    def __init__(self, elementDesc, name, label, description, group='allParams', advanced=False, semantic='', enabled=True, joinChar=' '):
        """
        :param elementDesc: the Attribute description of elements to store in that list
        """
        self._elementDesc = elementDesc
        self._joinChar = joinChar
        super(ListAttribute, self).__init__(name=name, label=label, description=description, value=[], uid=(), group=group, advanced=advanced, semantic=semantic, enabled=enabled)

    elementDesc = Property(Attribute, lambda self: self._elementDesc, constant=True)
    uid = Property(Variant, lambda self: self.elementDesc.uid, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)

    def validateValue(self, value):
        if JSValue is not None and isinstance(value, JSValue):
            # Note: we could use isArray(), property("length").toInt() to retrieve all values
            raise ValueError("ListAttribute.validateValue: cannot recognize QJSValue. Please, use JSON.stringify(value) in QML.")
        if isinstance(value, pyCompatibility.basestring):
            # Alternative solution to set values from QML is to convert values to JSON string
            # In this case, it works with all data types
            value = ast.literal_eval(value)

        if not isinstance(value, (list, tuple)):
            raise ValueError('ListAttribute only supports list/tuple input values (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))
        return value

    def matchDescription(self, value, strict=True):
        """ Check that 'value' content matches ListAttribute's element description. """
        if not super(ListAttribute, self).matchDescription(value, strict):
            return False
        # list must be homogeneous: only test first element
        if value:
            return self._elementDesc.matchDescription(value[0], strict)
        return True


class GroupAttribute(Attribute):
    """ A macro Attribute composed of several Attributes """
    def __init__(self, groupDesc, name, label, description, group='allParams', advanced=False, semantic='', enabled=True, joinChar=' '):
        """
        :param groupDesc: the description of the Attributes composing this group
        """
        self._groupDesc = groupDesc
        self._joinChar = joinChar
        super(GroupAttribute, self).__init__(name=name, label=label, description=description, value={}, uid=(), group=group, advanced=advanced, semantic=semantic, enabled=enabled)

    groupDesc = Property(Variant, lambda self: self._groupDesc, constant=True)

    def validateValue(self, value):
        """ Ensure value is compatible with the group description and convert value if needed. """
        if JSValue is not None and isinstance(value, JSValue):
            # Note: we could use isArray(), property("length").toInt() to retrieve all values
            raise ValueError("GroupAttribute.validateValue: cannot recognize QJSValue. Please, use JSON.stringify(value) in QML.")
        if isinstance(value, pyCompatibility.basestring):
            # Alternative solution to set values from QML is to convert values to JSON string
            # In this case, it works with all data types
            value = ast.literal_eval(value)

        if isinstance(value, dict):
            # invalidKeys = set(value.keys()).difference([attr.name for attr in self._groupDesc])
            # if invalidKeys:
            #     raise ValueError('Value contains key that does not match group description : {}'.format(invalidKeys))
            if self._groupDesc:
                commonKeys = set(value.keys()).intersection([attr.name for attr in self._groupDesc])
                if not commonKeys:
                    raise ValueError('Value contains no key that matches with the group description: {}'.format(commonKeys))
        elif isinstance(value, (list, tuple)):
            if len(value) != len(self._groupDesc):
                raise ValueError('Value contains incoherent number of values: desc size: {}, value size: {}'.format(len(self._groupDesc), len(value)))
        else:
            raise ValueError('GroupAttribute only supports dict/list/tuple input values (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))

        return value

    def matchDescription(self, value, strict=True):
        """
        Check that 'value' contains the exact same set of keys as GroupAttribute's group description
        and that every child value match corresponding child attribute description.

        Args:
            value: the value
            strict: strict test for the match (for instance, regarding a group with some parameter changes)
        """
        if not super(GroupAttribute, self).matchDescription(value):
            return False
        attrMap = {attr.name: attr for attr in self._groupDesc}

        matchCount = 0
        for k, v in value.items():
            # each child value must match corresponding child attribute description
            if k in attrMap and attrMap[k].matchDescription(v, strict):
                matchCount += 1

        if strict:
            return matchCount == len(value.items()) == len(self._groupDesc)

        return matchCount > 0

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
    def __init__(self, name, label, description, value, uid, group, advanced, semantic, enabled):
        super(Param, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced, semantic=semantic, enabled=enabled)


class File(Attribute):
    """
    """
    def __init__(self, name, label, description, value, uid, group='allParams', advanced=False, semantic='', enabled=True):
        super(File, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced, semantic=semantic, enabled=enabled)

    def validateValue(self, value):
        if not isinstance(value, pyCompatibility.basestring):
            raise ValueError('File only supports string input  (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))
        return os.path.normpath(value).replace('\\', '/') if value else ''


class BoolParam(Param):
    """
    """
    def __init__(self, name, label, description, value, uid, group='allParams', advanced=False, semantic='', enabled=True):
        super(BoolParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced, semantic=semantic, enabled=enabled)

    def validateValue(self, value):
        try:
            return bool(int(value))  # int cast is useful to handle string values ('0', '1')
        except:
            raise ValueError('BoolParam only supports bool value (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))


class IntParam(Param):
    """
    """
    def __init__(self, name, label, description, value, range, uid, group='allParams', advanced=False, semantic='', enabled=True):
        self._range = range
        super(IntParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced, semantic=semantic, enabled=enabled)

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
    def __init__(self, name, label, description, value, range, uid, group='allParams', advanced=False, semantic='', enabled=True):
        self._range = range
        super(FloatParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced, semantic=semantic, enabled=enabled)

    def validateValue(self, value):
        try:
            return float(value)
        except:
            raise ValueError('FloatParam only supports float value (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))

    range = Property(VariantList, lambda self: self._range, constant=True)


class ChoiceParam(Param):
    """
    """
    def __init__(self, name, label, description, value, values, exclusive, uid, group='allParams', joinChar=' ', advanced=False, semantic='', enabled=True):
        assert values
        self._values = values
        self._exclusive = exclusive
        self._joinChar = joinChar
        self._valueType = type(self._values[0])  # cast to value type
        super(ChoiceParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced, semantic=semantic, enabled=enabled)

    def conformValue(self, val):
        """ Conform 'val' to the correct type and check for its validity """
        val = self._valueType(val)
        if val not in self.values:
            raise ValueError('ChoiceParam value "{}" is not in "{}".'.format(val, str(self.values)))
        return val

    def validateValue(self, value):
        if self.exclusive:
            return self.conformValue(value)

        if not isinstance(value, pyCompatibility.Iterable):
            raise ValueError('Non exclusive ChoiceParam value should be iterable (param:{}, value:{}, type:{})'.format(self.name, value, type(value)))
        return [self.conformValue(v) for v in value]

    values = Property(VariantList, lambda self: self._values, constant=True)
    exclusive = Property(bool, lambda self: self._exclusive, constant=True)
    joinChar = Property(str, lambda self: self._joinChar, constant=True)


class StringParam(Param):
    """
    """
    def __init__(self, name, label, description, value, uid, group='allParams', advanced=False, semantic='', enabled=True):
        super(StringParam, self).__init__(name=name, label=label, description=description, value=value, uid=uid, group=group, advanced=advanced, semantic=semantic, enabled=enabled)

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
    documentation = ''
    category = 'Other'

    def __init__(self):
        pass

    def upgradeAttributeValues(self, attrValues, fromVersion):
        return attrValues

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
        if chunk.node.isParallelized and chunk.node.size > 1:
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

