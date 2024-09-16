__version__ = "2.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import os.path


class SfMAlignment(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmAlignment {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
This node allows to change the coordinate system of one SfM scene to align it on another one.

The alignment can be based on:
 * from_cameras_viewid: Align cameras in both SfM on the specified viewId
 * from_cameras_poseid: Align cameras in both SfM on the specified poseId
 * from_cameras_filepath: Align cameras with a filepath matching, using 'fileMatchingPattern'
 * from_cameras_metadata: Align cameras with matching metadata, using 'metadataMatchingList'
 * from_markers: Align from markers with the same Id

'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="Input SfMData file .",
            value="",
        ),
        desc.File(
            name="reference",
            label="Reference",
            description="Path to the scene used as the reference coordinate system.",
            value="",
        ),
        desc.ChoiceParam(
            name="method",
            label="Alignment Method",
            description="Alignment method:\n"
                        " - from_cameras_viewid: Align cameras with same view ID.\n"
                        " - from_cameras_poseid: Align cameras with same pose ID.\n"
                        " - from_cameras_filepath: Align cameras with a filepath matching, using 'fileMatchingPattern'.\n"
                        " - from_cameras_metadata: Align cameras with matching metadata, using 'metadataMatchingList'.\n"
                        " - from_markers: Align from markers with the same ID.\n"
                        " - from_landmarks: Align from matched features.\n",
            value="from_cameras_viewid",
            values=["from_cameras_viewid", "from_cameras_poseid", "from_cameras_filepath", "from_cameras_metadata", "from_markers", 'from_landmarks'],
        ),
        desc.StringParam(
            name="fileMatchingPattern",
            label="File Matching Pattern",
            description="Matching regular expression for the 'from_cameras_filepath' method.\n"
                        "You should capture specific parts of the filepath with parentheses to define matching elements.\n"
                        "Some examples of patterns:\n"
                        " - Match the filename without extension (default value): "
                        r'".*\/(.*?)\.\w{3}"' + "\n"
                        " - Match the filename suffix after '_': "
                        r'".*\/.*(_.*?\.\w{3})"' + "\n"
                        " - Match the filename prefix before '_': "
                        r'".*\/(.*?)_.*\.\w{3}"',
            value=r".*\/(.*?)\.\w{3}",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="metadataMatching",
                label="Metadata",
                description="",
                value="Metadata that should match to create the correspondences.",
            ),
            name="metadataMatchingList",
            label="Metadata Matching List",
            description="List of metadata that should match to create the correspondences.\n"
                        "If the list is empty, the default value will be used: ['Make', 'Model', 'Exif:BodySerialNumber', 'Exif:LensSerialNumber'].",
        ),
        desc.BoolParam(
            name="applyScale",
            label="Scale",
            description="Apply scale transformation.",
            value=True,
        ),
        desc.BoolParam(
            name="applyRotation",
            label="Rotation",
            description="Apply rotation transformation.",
            value=True,
        ),
        desc.BoolParam(
            name="applyTranslation",
            label="Translation",
            description="Apply translation transformation.",
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
            label="SfMData File",
            description="Output SfMData file.",
            value=lambda attr: desc.Node.internalFolder + (os.path.splitext(os.path.basename(attr.node.input.value))[0] or "sfmData") + ".abc",
        ),
        desc.File(
            name="outputViewsAndPoses",
            label="Poses",
            description="Path to the output SfMData file with cameras (views and poses).",
            value=desc.Node.internalFolder + "cameras.sfm",
        ),
    ]
