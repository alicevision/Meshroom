__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class DepthMapRendering(desc.AVCommandLineNode):
    commandLine = "aliceVision_depthMapRendering {allParams}"

    category = "Utils"
    documentation = """
    Using camera parameters and mesh, render depthmaps for each view
    """

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="mesh",
            label="Input Mesh",
            description="Input mesh file.",
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
            label="Folder",
            description="Output folder.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="depth",
            label="Depth Maps",
            description="Rendered depth maps.",
            semantic="image",
            value=desc.Node.internalFolder + "<VIEW_ID>_depthMap.exr",
            group="",  # do not export on the command line
        ),
        desc.File(
            name="mask",
            label="Masks",
            description="Masks.",
            semantic="image",
            value=desc.Node.internalFolder + "<VIEW_ID>_mask.exr",
            group="",  # do not export on the command line
        ),
    ]
