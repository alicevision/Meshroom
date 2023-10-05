__version__ = "1.0"

from meshroom.core import desc
import os.path

class SfmMerge(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmMerge {allParams}'
    size = desc.DynamicNodeSize('firstinput')

    category = 'Utils'
    documentation = '''
Merge two sfmData into a single one. Fails if some uid is shared among them
'''

    inputs = [
        desc.File(
            name="firstinput",
            label="SfMData",
            description="First Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.File(
            name="secondinput",
            label="SfMData",
            description="Second Input SfMData file.",
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
        )
    ]

    outputs = [
        desc.File(
            name="output",
            label="SfMData",
            description="Path to the output SfM file (in SfMData format).",
            value=lambda attr: desc.Node.internalFolder + "sfmData.sfm",
            uid=[],
        ),
    ]
