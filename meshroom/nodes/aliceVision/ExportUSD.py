__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ExportUSD(desc.AVCommandLineNode):
    commandLine = 'aliceVision_exportUSD {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
    Export a mesh (OBJ file) to USD format.
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="Input mesh file.",
            value="",
        ),
        desc.ChoiceParam(
            name="fileType",
            label="USD File Format",
            description="Output USD file format.",
            value="usda",
            values=["usda", "usdc", "usdz"]
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
            description="Path to the output file.",
            value="{nodeCacheFolder}/output.{fileTypeValue}",
        ),
    ]
