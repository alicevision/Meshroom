__version__ = "1.0"


import logging
from meshroom.core import desc


LOGGER = logging.getLogger("TestSubmit")


class PluginSubmitterA(desc.BaseNode):
    """
    Test process no parallelization
    """
    parallelization = None
    
    inputs = [
        desc.IntParam(
            name="input",
            label="Input",
            description="input",
            value=1,
        ),
    ]
    outputs = [
        desc.IntParam(
            name="output",
            label="Output",
            description="Output",
            value=None,
        ),
    ]

    def processChunk(self, chunk):
        iteration = chunk.range.iteration
        nbBlocks = chunk.range.nbBlocks
        LOGGER.info(f"> Process chunk {iteration}/{nbBlocks}")
        LOGGER.info(f"> Done")


class PluginSubmitterB(PluginSubmitterA):
    """
    Test process with parallelization adn static node size
    """
    size = desc.StaticNodeSize(2)
    parallelization = desc.Parallelization(blockSize=1)


class PluginSubmitterC(PluginSubmitterA):
    """
    Test process with parallelization and dynamic node size
    """
    size = desc.DynamicNodeSize("input")
    parallelization = desc.Parallelization(blockSize=1)
