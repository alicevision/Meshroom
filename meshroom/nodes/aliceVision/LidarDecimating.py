__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

class LidarDecimating(desc.AVCommandLineNode):
    commandLine = 'aliceVision_lidarDecimating {allParams}'

    size = desc.StaticNodeSize(10)
    parallelization = desc.Parallelization(blockSize=1)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeFullSize}'

    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Dense Reconstruction'
    documentation = '''
    This node simplifies previously reconstructed meshes from Lidar.
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input JSON",
            description="Input JSON file with description of inputs.",
            value="",
        ),
        desc.FloatParam(
            name="errorLimit",
            label="Error Limit",
            description="Maximal distance (in meters) allowed.",
            value=0.001,
            range=(0.0, 1.0, 0.001),
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
            label="Sub-Meshes Directory",
            description="Output directory for sub-meshes.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="outputJson",
            label="Scene Description",
            description="Output scene description.",
            value=desc.Node.internalFolder + "scene.json",
        ),
    ]
