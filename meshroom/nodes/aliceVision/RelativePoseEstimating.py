__version__ = "3.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL

class RelativePoseEstimating(desc.AVCommandLineNode):
    commandLine = 'aliceVision_relativePoseEstimating {allParams}'
    size = desc.DynamicNodeSize('input')
    
    parallelization = desc.Parallelization(blockSize=25)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Sparse Reconstruction'
    documentation = '''
Estimate relative pose between each pair of views that share tracks.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="SfMData file.",
            value="",
        ),
        desc.File(
            name="tracksFilename",
            label="Tracks File",
            description="Tracks file.",
            value="",
        ),
        desc.BoolParam(
            name="enforcePureRotation",
            label="Enforce pure rotation",
            description="Enforce pure rotation as a model",
            value=False,
        ),
        desc.IntParam(
            name="countIterations",
            label="Ransac Max Iterations",
            description="Maximal number of iterations.",
            value=1024,
            range=(1024, 500000, 1),
            advanced=True,
        ),
        desc.IntParam(
            name="minInliers",
            label="Ransac Min Inliers",
            description="Minimal allowed inliers in two view relationship.",
            value=35,
            range=(1, 1000, 1),
            advanced=True,
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
            label="Pairs Info",
            description="Path to the output Pairs info files directory.",
            value=desc.Node.internalFolder,
        ),
    ]
