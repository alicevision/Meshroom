__version__ = "2.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class ConvertSfMFormat(desc.AVCommandLineNode):
    commandLine = 'aliceVision_convertSfMFormat {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
Convert an SfM scene from one file format to another.
It can also be used to remove specific parts of from an SfM scene (like filter all 3D landmarks or filter 2D observations).
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="Input SfMData file.",
            value="",
        ),
        desc.ChoiceParam(
            name="fileExt",
            label="SfM File Format",
            description="Output SfM file format.",
            value="abc",
            values=["abc", "sfm", "json", "ply", "baf"],
            group="",  # exclude from command line
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types to keep.",
            values=DESCRIBER_TYPES,
            value=["dspsift"],
            exclusive=False,
            joinChar=",",
            exposed=True,
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="imageId",
                label="Image ID",
                description="UID or path of an image to add to the white list.",
                value="",
            ),
            name="imageWhiteList",
            label="Image White List",
            description="Image white list (UIDs or image paths).",
        ),
        desc.BoolParam(
            name="views",
            label="Views",
            description="Export views.",
            value=True,
        ),
        desc.BoolParam(
            name="intrinsics",
            label="Intrinsics",
            description="Export intrinsics.",
            value=True,
        ),
        desc.BoolParam(
            name="extrinsics",
            label="Extrinsics",
            description="Export extrinsics.",
            value=True,
        ),
        desc.BoolParam(
            name="structure",
            label="Structure",
            description="Export structure.",
            value=True,
        ),
        desc.BoolParam(
            name="observations",
            label="Observations",
            description="Export observations.",
            value=True,
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
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfm.{fileExtValue}",
        ),
    ]
