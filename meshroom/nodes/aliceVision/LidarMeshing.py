__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

class LidarMeshing(desc.AVCommandLineNode):
    commandLine = 'aliceVision_lidarMeshing {allParams}'

    # size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=2)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Dense Reconstruction'
    documentation = '''
    This node creates a dense geometric surface representation of the lidar measurements.
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input JSON",
            description="Input JSON file with description of inputs.",
            value="",
            uid=[0],
        ),
        desc.BoolParam(
            name="useBoundingBox",
            label="Custom Bounding Box",
            description="Edit the meshing bounding box.\n"
                        "If enabled, it takes priority over the 'Estimate Space From SfM' option.\n"
                        "Parameters can be adjusted in advanced settings.",
            value=False,
            uid=[0],
            group="",
        ),
        desc.GroupAttribute(
            name="boundingBox",
            label="Bounding Box Settings",
            description="Translation, rotation and scale of the bounding box.",
            groupDesc=[
                desc.GroupAttribute(
                    name="bboxTranslation",
                    label="Translation",
                    description="Position in space.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="X offset.",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Y offset.",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Z offset.",
                            value=0.0,
                            uid=[0],
                            range=(-20.0, 20.0, 0.01),
                        ),
                    ],
                    joinChar=",",
                ),
                desc.GroupAttribute(
                    name="bboxRotation",
                    label="Euler Rotation",
                    description="Rotation in Euler degrees.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="Euler X rotation.",
                            value=0.0,
                            uid=[0],
                            range=(-90.0, 90.0, 1.0)
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Euler Y rotation.",
                            value=0.0,
                            uid=[0],
                            range=(-180.0, 180.0, 1.0)
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Euler Z rotation.",
                            value=0.0,
                            uid=[0],
                            range=(-180.0, 180.0, 1.0)
                        ),
                    ],
                    joinChar=",",
                ),
                desc.GroupAttribute(
                    name="bboxScale",
                    label="Scale",
                    description="Scale of the bounding box.",
                    groupDesc=[
                        desc.FloatParam(
                            name="x", label="x", description="X scale.",
                            value=1.0,
                            uid=[0],
                            range=(0.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="y", label="y", description="Y scale.",
                            value=1.0,
                            uid=[0],
                            range=(0.0, 20.0, 0.01),
                        ),
                        desc.FloatParam(
                            name="z", label="z", description="Z scale.",
                            value=1.0,
                            uid=[0],
                            range=(0.0, 20.0, 0.01),
                        ),
                    ],
                    joinChar=",",
                ),
            ],
            joinChar=",",
            enabled=lambda node: node.useBoundingBox.value,
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
            name="output",
            label="Sub-Meshes directory",
            description="Output directory for sub-meshes",
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name="outputJson",
            label="Scene description",
            description="Output Scene description.",
            value=desc.Node.internalFolder + "scene.json",
            uid=[],
        ),
    ]
