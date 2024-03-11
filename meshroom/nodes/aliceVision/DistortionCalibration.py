__version__ = '3.0'

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class DistortionCalibration(desc.AVCommandLineNode):
    commandLine = 'aliceVision_distortionCalibration {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Other'
    documentation = '''
Calibration of a camera/lens couple distortion using a full screen checkerboard.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="SfMData file.",
            value="",
            uid=[0],
        ),
        desc.File(
            name="checkerboards",
            label="Checkerboards Folder",
            description="Folder containing checkerboard JSON files.",
            value="",
            uid=[0],
        ),
        desc.ChoiceParam(
            name="cameraModel",
            label="Camera Model",
            description="Camera model used to estimate distortion.",
            value="3deanamorphic4",
            values=["3deanamorphic4"],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="SfMData File",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfmData.sfm",
            uid=[],
        ),
    ]
