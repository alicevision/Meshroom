__version__ = "1.0"

from meshroom.core import desc
import os.path


class MergeNodeSize(object):
    """
    MergeNodeSize expresses a dependency to two input attributess to define
    the size of a Node in terms of individual tasks for parallelization.
    """
    def __init__(self, param1, param2):
        self._param1 = param1
        self._param2 = param2

    def computeSize(self, node):
        
        size1 = 0
        size2 = 0

        param1 = node.attribute(self._param1)
        if param1.isLink:
            size1 = param1.getLinkParam().node.size

        param2 = node.attribute(self._param2)
        if param2.isLink:
            size2 = param2.getLinkParam().node.size
        
        return size1 + size2


class SfmMerge(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmMerge {allParams}'
    size = MergeNodeSize('firstinput', 'secondinput')

    category = 'Utils'
    documentation = '''
Merge two sfmData into a single one. Fails if some uid is shared among them
'''

    inputs = [
        desc.File(
            name="firstinput",
            label="SfMData",
            description="First Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.File(
            name="secondinput",
            label="SfMData",
            description="Second Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            value="info",
            values=["fatal", "error", "warning", "info", "debug", "trace"],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name="output",
            label="SfMData",
            description="Path to the output SfM file (in SfMData format).",
            value=lambda attr: desc.Node.internalFolder + "sfmData.sfm",
            uid=[],
        ),
    ]
