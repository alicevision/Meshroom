__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ConvertDistortion(desc.AVCommandLineNode):
    commandLine = 'aliceVision_convertDistortion {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
    Convert distortions between different models.
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="Input SfMData file.",
            value="",
        ),
        desc.ChoiceParam(
            name="from",
            label="From",
            description="Distortion model to convert from.",
            value="distortion",
            values=["distortion", "undistortion"],
        ),
        desc.ChoiceParam(
            name="to",
            label="To",
            description="Distortion model to convert to.",
            value="undistortion",
            values=["distortion", "undistortion"],
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
            value=desc.Node.internalFolder + "sfm.abc",
        ),
    ]
