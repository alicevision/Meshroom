__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

class LidarMerging(desc.AVCommandLineNode):
    commandLine = 'aliceVision_lidarMerging {allParams}'

    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Dense Reconstruction'
    documentation = '''
    This node merge several meshes into one.
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input JSON",
            description="Input JSON file with description of inputs.",
            value="",
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
            label="Mesh Path Output",
            description="Output directory for mesh.",
            value=desc.Node.internalFolder + "output.obj",
        ),
    ]
