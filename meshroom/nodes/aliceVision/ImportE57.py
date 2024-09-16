__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ImportE57(desc.AVCommandLineNode):
    commandLine = 'aliceVision_importE57 {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
Import an E57 file and generate an SfMData.
'''

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="inputFile",
                label="E57 File",
                description="Path to an E57 file.",
                value="",
            ),
            name="input",
            label="Input Files",
            description="Set of E57 files in the same reference frame.",
        ),
        desc.FloatParam(
            name="maxDensity",
            label="Points Density",
            description="Ensure each point has no neighbour closer than maxDensity meters.",
            value=0.01,
            range=(0.0, 0.2, 0.001),
        ),
        desc.FloatParam(
            name="minIntensity",
            label="Laser Intensity Lower Limit",
            description="Ensure no point has an intensity lower than this value.",
            value=0.03,
            range=(0.0, 1.0, 0.01),
        ),
        desc.IntParam(
            name="maxPointsPerBlock",
            label="Points Limit",
            description="Limit the number of points per computation region (For memory usage, 0 means no limit).",
            value=5000000,
            range=(0, 10000000, 100000),
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
            description="Path to the output JSON file.",
            value=desc.Node.internalFolder + "inputset.json",
        ),
    ]
