__version__ = "2.1"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import os.path


class SfMTransfer(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmTransfer {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
This node allows to transfer poses and/or intrinsics form one SfM scene onto another one.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file.",
            value="",
            uid=[0],
        ),
        desc.File(
            name="reference",
            label="Reference",
            description="Path to the scene used as the reference to retrieve resolved poses and intrinsics.",
            value="",
            uid=[0],
        ),
        desc.ChoiceParam(
            name="method",
            label="Matching Method",
            description="Matching Method:\n"
                " - from_viewid: Align cameras with same view ID.\n"
                " - from_filepath: Align cameras with a filepath matching, using 'fileMatchingPattern'.\n"
                " - from_metadata: Align cameras with matching metadata, using 'metadataMatchingList'.\n"
                " - from_intrinsicid: Copy intrinsics parameters.\n",
            value="from_viewid",
            values=["from_viewid", "from_filepath", "from_metadata", "from_intrinsicid"],
            exclusive=True,
            uid=[0],
        ),
        desc.StringParam(
            name="fileMatchingPattern",
            label="File Matching Pattern",
            description="Matching regular expression for the 'from_cameras_filepath' method.\n"
                        "You should capture specific parts of the filepath with parentheses to define matching elements.\n"
                        "Some examples of patterns:\n"
                        " - Match the filename without extension (default value): "
                        r'".*\/(.*?)\.\w{3}"' + "\n"
                        " - Match the filename suffix after \"_\": "
                        r'".*\/.*(_.*?\.\w{3})"' + "\n"
                        " - Match the filename prefix before \"_\": "
                        r'".*\/(.*?)_.*\.\w{3}"',
            value=r'.*\/(.*?)\.\w{3}',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="metadataMatching",
                label="Metadata",
                description="Metadata that should match to create correspondences.",
                value="",
                uid=[0],
            ),
            name="metadataMatchingList",
            label="Metadata Matching List",
            description="List of metadata that should match to create the correspondences.\n"
                        "If the list is empty, the default value will be used:\n"
                        "['Make', 'Model', 'Exif:BodySerialNumber', 'Exif:LensSerialNumber'].",
        ),
        desc.BoolParam(
            name="transferPoses",
            label="Poses",
            description="Transfer poses.",
            value=True,
            uid=[0]
        ),
        desc.BoolParam(
            name="transferIntrinsics",
            label="Intrinsics",
            description="Transfer cameras intrinsics.",
            value=True,
            uid=[0]
        ),
        desc.BoolParam(
            name="transferLandmarks",
            label="Landmarks",
            description="Transfer landmarks.",
            value=True,
            uid=[0]
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
            label="SfMData",
            description="Path to the output SfM point cloud file (in SfMData format).",
            value=lambda attr: desc.Node.internalFolder + (os.path.splitext(os.path.basename(attr.node.input.value))[0] or "sfmData") + ".abc",
            uid=[],
        ),
        desc.File(
            name="outputViewsAndPoses",
            label="Poses",
            description="Path to the output SfMData file with cameras (views and poses).",
            value=desc.Node.internalFolder + "cameras.sfm",
            uid=[],
        ),
    ]
