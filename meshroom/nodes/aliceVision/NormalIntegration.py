__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

class NormalIntegration(desc.CommandLineNode):
    commandLine = 'aliceVision_normalIntegration {allParams}'
    category = 'Photometry'
    documentation = '''
TODO.
'''

    inputs = [
        desc.File(
            name="inputPath",
            label="Normal Maps Folder",
            description="Path to the folder containing the normal maps and the masks.",
            value="",
            uid=[0],
         ),
        desc.File(
            name="sfmDataFile",
            label="SfMData",
            description="Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.IntParam(
            name="downscale",
            label="Downscale Factor",
            description="Downscale factor for faster results.",
            value=1,
            range=(1, 10, 1),
            advanced=True,
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
            name="outputPath",
            label="Output Path",
            description="Path to the output folder.",
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
