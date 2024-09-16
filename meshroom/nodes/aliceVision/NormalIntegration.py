__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

class NormalIntegration(desc.CommandLineNode):
    commandLine = 'aliceVision_normalIntegration {allParams}'
    category = 'Photometric Stereo'
    documentation = '''
Evaluate a depth map from a normals map (currently in development)
'''

    inputs = [
        desc.File(
            name="inputPath",
            label="Normal Maps Folder",
            description="Path to the folder containing the normal maps and the masks.",
            value="",
         ),
        desc.File(
            name="sfmDataFile",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.IntParam(
            name="downscale",
            label="Downscale Factor",
            description="Downscale factor for faster results.",
            value=1,
            range=(1, 10, 1),
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
            name="depthMap",
            label="Depth Map Camera",
            description="Generated depth in the camera coordinate system.",
            semantic="image",
            value=desc.Node.internalFolder + "<POSE_ID>_depthMap.exr",
            group="", # do not export on the command line
        )
    ]
