__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ImportKnownPoses(desc.AVCommandLineNode):
    commandLine = 'aliceVision_importKnownPoses {allParams}'
    size = desc.DynamicNodeSize('sfmData')

    documentation = '''
    Import known poses from various file formats like xmp or json.
    '''

    inputs = [
        desc.File(
            name="sfmData",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="knownPosesData",
            label="Known Poses Data",
            description="Known poses data in the JSON or XMP format.",
            value="",
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
            label="Output",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "/sfmData.abc",
        ),
    ]
