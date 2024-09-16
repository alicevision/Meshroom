__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ApplyCalibration(desc.AVCommandLineNode):
    commandLine = "aliceVision_applyCalibration {allParams}"
    size = desc.DynamicNodeSize("input")

    category = "Utils"
    documentation = """ Overwrite intrinsics with a calibrated intrinsic. """

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="calibration",
            label="Calibration",
            description="Calibration file (SfmData or Lens calibration file).",
            value="",
        ),
        desc.BoolParam(
            name="useJson",
            label="Use Lens Calibration File",
            description="Calibration is a Lens calibration file generated using 3Dequalizer instead of an sfmData.",
            value=False,
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
            label="SMData",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfmData.sfm",
        ),
    ]
