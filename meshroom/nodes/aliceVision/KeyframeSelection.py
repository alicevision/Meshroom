__version__ = "2.0"

import os
from meshroom.core import desc


class KeyframeSelection(desc.AVCommandLineNode):
    commandLine = 'aliceVision_keyframeSelection {allParams}'

    category = 'Utils'
    documentation = '''
Allows to extract keyframes from a video and insert metadata.
It can extract frames from a synchronized multi-cameras rig.

You can extract frames at regular interval by configuring only the min/maxFrameStep.
'''

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="mediaPath",
                label="Media Path",
                description="Media path.",
                value="",
                uid=[0],
            ),
            name="mediaPaths",
            label="Media Paths",
            description="Input video files or image sequence directories.",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="brand",
                label="Brand",
                description="Camera brand.",
                value="",
                uid=[0],
            ),
            name="brands",
            label="Brands",
            description="Camera brands."
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="model",
                label="Model",
                description="Camera model.",
                value="",
                uid=[0],
            ),
            name="models",
            label="Models",
            description="Camera models."
        ),
        desc.ListAttribute(
            elementDesc=desc.FloatParam(
                name="mmFocal",
                label="mmFocal",
                description="Focal in mm (will be used if not 0).",
                value=0.0,
                range=(0.0, 500.0, 1.0),
                uid=[0],
            ),
            name="mmFocals",
            label="mmFocals",
            description="Focals in mm (will be used if not 0)."
        ),
        desc.File(
            name="sensorDbPath",
            label="Sensor Db Path",
            description="Camera sensor width database path.",
            value="${ALICEVISION_SENSOR_DB}",
            uid=[0],
        ),
        desc.GroupAttribute(
            name="regularSelection",
            label="Regular Keyframe Selection",
            description="Parameters for the regular keyframe selection.\nKeyframes are selected regularly over the sequence with respect to the set parameters.",
            group=None,  # skip group from command line
            groupDesc=[
                desc.BoolParam(
                    name="useRegularSelection",
                    label="Use Regular Selection",
                    description="Enable and use the regular keyframe selection.",
                    value=True,
                    uid=[0],
                    enabled=False,  # only method for now, it must always be enabled
                ),
                desc.IntParam(
                    name="minFrameStep",
                    label="Min Frame Step",
                    description="Minimum number of frames between two keyframes.",
                    value=12,
                    range=(1, 1000, 1),
                    uid=[0],
                    enabled=lambda node: node.regularSelection.useRegularSelection.value
                ),
                desc.IntParam(
                    name="maxFrameStep",
                    label="Max Frame Step",
                    description="Maximum number of frames between two keyframes. Ignored if equal to 0.",
                    value=0,
                    range=(0, 1000, 1),
                    uid=[0],
                    enabled=lambda node: node.regularSelection.useRegularSelection.value
                ),
                desc.IntParam(
                    name="maxNbOutFrames",
                    label="Max Nb Output Frames",
                    description="Maximum number of output frames (0 = no limit).\n"
                                "'minFrameStep' and 'maxFrameStep' will always be respected, so combining them with this parameter\n"
                                "might cause the selection to stop before reaching the end of the input sequence(s).",
                    value=0,
                    range=(0, 10000, 1),
                    uid=[0],
                    enabled=lambda node: node.regularSelection.useRegularSelection.value
                ),
            ],
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            value="info",
            values=["fatal", "error", "warning", "info", "debug", "trace"],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name="outputFolder",
            label="Folder",
            description="Output keyframes folder for extracted frames.",
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]

