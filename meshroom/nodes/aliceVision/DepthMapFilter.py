__version__ = "4.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class DepthMapFilter(desc.AVCommandLineNode):
    commandLine = 'aliceVision_depthMapFiltering {allParams}'
    gpu = desc.Level.NORMAL
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=24)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Dense Reconstruction'
    documentation = '''
Filter depth map values that are not coherent in multiple depth maps.
This allows to filter unstable points before starting the fusion of all depth maps in the Meshing node.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="SfMData file.",
            value="",
        ),
        desc.File(
            name="depthMapsFolder",
            label="Depth Maps Folder",
            description="Input depth maps folder.",
            value="",
        ),
        desc.FloatParam(
            name="minViewAngle",
            label="Min View Angle",
            description="Minimum angle between two views.",
            value=2.0,
            range=(0.0, 10.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="maxViewAngle",
            label="Max View Angle",
            description="Maximum angle between two views.",
            value=70.0,
            range=(10.0, 120.0, 1.0),
            advanced=True,
        ),
        desc.IntParam(
            name="nNearestCams",
            label="Number Of Nearest Cameras",
            description="Number of nearest cameras used for filtering.",
            value=10,
            range=(0, 20, 1),
            advanced=True,
        ),
        desc.IntParam(
            name="minNumOfConsistentCams",
            label="Min Consistent Cameras",
            description="Minimum number of consistent cameras.",
            value=3,
            range=(0, 10, 1),
        ),
        desc.IntParam(
            name="minNumOfConsistentCamsWithLowSimilarity",
            label="Min Consistent Cameras Bad Similarity",
            description="Minimum number of consistent cameras for pixels with weak similarity value.",
            value=4,
            range=(0, 10, 1),
        ),
        desc.FloatParam(
            name="pixToleranceFactor",
            label="Tolerance Size",
            description="Filtering tolerance size factor, in pixels.",
            value=2.0,
            range=(0.001, 10.0, 0.1),
            advanced=True,
        ),
        desc.IntParam(
            name="pixSizeBall",
            label="Filtering Size",
            description="Filtering size in pixels.",
            value=0,
            range=(0, 10, 1),
            advanced=True,
        ),
        desc.IntParam(
            name="pixSizeBallWithLowSimilarity",
            label="Filtering Size Bad Similarity",
            description="Filtering size in pixels for low similarity.",
            value=0,
            range=(0, 10, 1),
            advanced=True,
        ),
        desc.BoolParam(
            name="computeNormalMaps",
            label="Compute Normal Maps",
            description="Compute normal maps for each depth map.",
            value=False,
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
            label="Filtered Depth Maps Folder",
            description="Output folder for generated depth maps.",
            value=desc.Node.internalFolder,
        ),
        # these attributes are only here to describe more accurately the output of the node
        # by specifying that it generates 2 sequences of images
        # (see in Viewer2D.qml how these attributes can be used)
        desc.File(
            name="depth",
            label="Depth Maps",
            description="Filtered depth maps.",
            semantic="image",
            value=desc.Node.internalFolder + "<VIEW_ID>_depthMap.exr",
            group="",  # do not export on the command line
        ),
        desc.File(
            name="sim",
            label="Sim Maps",
            description="Filtered sim maps.",
            semantic="image",
            value=desc.Node.internalFolder + "<VIEW_ID>_simMap.exr",
            group="",  # do not export on the command line
        ),
        desc.File(
            name="normal",
            label="Normal Maps",
            description="Normal maps.",
            semantic="image",
            value=desc.Node.internalFolder + "<VIEW_ID>_normalMap.exr",
            enabled=lambda node: node.computeNormalMaps.value,
            group="",  # do not export on the command line
        ),
    ]
