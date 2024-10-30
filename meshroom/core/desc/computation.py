import math
from enum import Enum

from .attribute import ListAttribute, IntParam


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
