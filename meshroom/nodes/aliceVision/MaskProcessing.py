__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL

import os.path

class MaskProcessingNodeSize(desc.DynamicNodeSize):
    """
    MaskProcessingNodeSize expresses a dependency to multiple input attributess to define
    the size of a Node in terms of individual tasks for parallelization.
    """
    def __init__(self, param):
        self._params = param

    def computeSize(self, node):
        
        size = 0

        for input in node.attribute(self._params).value:
            paramName = input.getFullName()
            param = node.attribute(paramName)
            if param.isLink:
                size = max(size, param.getLinkParam().node.size)
        
        return size


class MaskProcessing(desc.AVCommandLineNode):
    commandLine = 'aliceVision_maskProcessing {allParams}'
    size = MaskProcessingNodeSize("inputs")

    category = 'Utils'
    documentation = '''
    Perform operations on a list of masks with the same names
    '''

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="input",
                label="Input Directory",
                description="A directory with a set of mask.",
                value="",
            ),
            name="inputs",
            label="Input directories",
            description="A set of directories containing masks with the same names.",
            exposed=True,
        ),
        desc.ChoiceParam(
            name="operator",
            label="Operator",
            description="Operator: Binary operator\n"
                        "OR : applies binary OR between all the masks\n"
                        "AND : applies binary AND between all the masks\n"
                        "NOT : applies binary NOT to the first mask in the list\n",
            value="and",
            values=["or", "and", "not"],
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        )
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Path to the output directory.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="masks",
            label="Masks",
            description="Processed segmentation masks.",
            semantic="imageList",
            value= desc.Node.internalFolder + "*.exr",
            group="",
        ),
    ]
