__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

class ApplyCalibration(desc.AVCommandLineNode):
    commandLine = 'aliceVision_applyCalibration {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
Overwrite intrinsics with a calibrated intrinsic.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.File(
            name="calibration",
            label="Calibration",
            description="Calibration file (Either SfmData or Lens calibration file).",
            value="",
            uid=[0],
        ),
        desc.BoolParam(
            name="useJson",
            label="Use lens calibration file",
            description="Use Lens calibration file generated using 3Dequalizer.",
            value=False,
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
            label="SMData",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfmData.sfm",
            uid=[],
        ),
    ]
