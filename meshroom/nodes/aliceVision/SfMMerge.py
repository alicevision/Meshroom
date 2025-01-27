__version__ = "3.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL

import os.path

class MergeNodeSize(desc.DynamicNodeSize):
    """
    MergeNodeSize expresses a dependency to multiple input attributess to define
    the size of a Node in terms of individual tasks for parallelization.
    """
    def __init__(self, param):
        self._params = param

    def computeSize(self, node):
        
        size = 0

        for input in node.attribute(self._params).value:
            paramName = input.getFullName()
            param = node.attribute(paramName)
            size = size + param.getLinkParam().node.size
        
        return size


class SfMMerge(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmMerge {allParams}'
    size = MergeNodeSize("inputs")

    category = 'Utils'
    documentation = '''
Merges two SfMData files into a single one. Fails if some UID is shared among them.
'''

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="input",
                label="Input SfmData",
                description="A SfmData file.",
                value="",
            ),
            name="inputs",
            label="Inputs",
            description="Set of SfmData (at least 1 is required).",
            exposed=True,
        ),
        desc.ChoiceParam(
            name="method",
            label="Merge Method",
            description="Merge method:\n"
                        " - simple copy: Straight copy without duplicate management.\n"
                        " - from_landmarks: Align from matched features, try to fuse.\n",
            value="simple_copy",
            values=["simple_copy", 'from_landmarks'],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="matchesFolder",
                label="Matches Folder",
                description="",
                value="",
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which the computed matches are stored.",
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types used to describe an image.",
            values=DESCRIBER_TYPES,
            value=["dspsift"],
            exclusive=False,
            joinChar=",",
        ),
        desc.ChoiceParam(
            name="fileExt",
            label="SfM File Format",
            description="Output SfM file format.",
            value="abc",
            values=["abc", "sfm", "json"],
            group="",  # exclude from command line
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
            label="SfMData",
            description="Path to the output SfM file (in SfMData format).",
            value=lambda attr: desc.Node.internalFolder + "sfmData.{fileExtValue}",
        )
    ]
