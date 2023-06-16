__version__ = "1.0"

from meshroom.core import desc

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
            description="Calibration SfMData file.",
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
