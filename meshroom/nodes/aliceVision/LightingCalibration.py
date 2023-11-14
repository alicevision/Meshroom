__version__ = "1.0"

from meshroom.core import desc


class LightingCalibration(desc.CommandLineNode):
    commandLine = 'aliceVision_lightingCalibration {allParams}'
    category = 'Photometry'
    documentation = '''
Evaluate the lighting in a scene using spheres placed in the scene.
Can also be used to calibrate a lighting dome (RTI type).
'''

    inputs = [
        desc.File(
            name="inputPath",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
            uid=[0]
        ),
        desc.File(
            name="inputJSON",
            label="Sphere Detection File",
            description="Input JSON file containing sphere centers and radiuses.",
            value="",
            uid=[0]
        ),
        desc.BoolParam(
            name="saveAsModel",
            label="Save As Model",
            description="Check if this calibration file will be used with other datasets.",
            value=False,
            uid=[0]
        ),
        desc.ChoiceParam(
            name="method",
            label="Calibration Method",
            description="Method used for light calibration.\n"
                        "Use 'brightestPoint' for shiny spheres and 'whiteSphere' for white matte spheres.",
            values=["brightestPoint", "whiteSphere"],
            value="brightestPoint",
            exclusive=True,
            uid=[0]
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
            name="outputFile",
            label="Light File",
            description="Light information will be written here.",
            value=desc.Node.internalFolder + "/lights.json",
            uid=[]
        )
    ]
