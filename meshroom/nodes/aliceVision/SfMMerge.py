__version__ = "2.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL

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


class SfMMerge(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmMerge {allParams}'
    size = MergeNodeSize('firstinput', 'secondinput')

    category = 'Utils'
    documentation = '''
Merges two SfMData files into a single one. Fails if some UID is shared among them.
'''

    inputs = [
        desc.File(
            name="firstinput",
            label="First SfMData",
            description="First input SfMData file to merge.",
            value="",
        ),
        desc.File(
            name="secondinput",
            label="Second SfMData",
            description="Second input SfMData file to merge.",
            value="",
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
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="SfMData",
            description="Path to the output SfM file (in SfMData format).",
            value=lambda attr: desc.Node.internalFolder + "sfmData.sfm",
        ),
    ]
