__version__ = "1.0"


import logging
from meshroom.core import desc


LOGGER = logging.getLogger("TestSubmit")


class PluginSubmitterA(desc.Node):
    """
    Test process no parallelization
    """
    parallelization = None
    
    inputs = [
        desc.IntParam(
            name="nbChunks",
            label="nbChunks",
            description="Nb Chunks",
            value=1,
            exposed=True
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="inputfile",
                label="Input file",
                description="",
                value="",
            ),
            name="inputs",
            label="inputs",
            description="inputs",
            exposed=True,
        ),
    ]
    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Output",
            value="",
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

    def postprocess(self, node):
        LOGGER.info(f"> PluginSubmitterB postprocess Done")


class PluginSubmitterC(PluginSubmitterA):
    """
    Test process with parallelization and dynamic node size
    """
    size = desc.DynamicNodeSize("nbChunks")
    parallelization = desc.Parallelization(blockSize=1)
    
    def preprocess(self, node):
        LOGGER.info(f"> PluginSubmitterC preprocess Done")

    def postprocess(self, node):
        LOGGER.info(f"> PluginSubmitterC postprocess Done")
