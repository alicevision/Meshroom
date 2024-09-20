__version__ = '1.0'

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class CheckerboardCalibration(desc.AVCommandLineNode):
    commandLine = 'aliceVision_checkerboardCalibration {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Other'
    documentation = '''
Estimate the camera intrinsics and extrinsincs on a set of checkerboard images.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="SfMData file.",
            value="",
        ),
        desc.File(
            name="checkerboards",
            label="Checkerboards Folder",
            description="Folder containing checkerboard JSON files.",
            value="",
        ),
        desc.FloatParam(
            name="squareSize",
            label="Square Size",
            description="Checkerboard square width in mm",
            value=10.,
            range=(0.1, 100., 0.1),
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
            label="SfMData File",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfmData.sfm",
        )
    ]
