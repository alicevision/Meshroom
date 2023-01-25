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
            name="selectionMethod",
            label="Keyframe Selection Method",
            description="Selection the regular or smart method for the keyframe selection.\n"
                        "- With the regular method, keyframes are selected regularly over the sequence with respect to the set parameters.\n"
                        "- With the smart method, keyframes are selected based on their sharpness and optical flow scores.",
            group=None,  # skip group from command line
            groupDesc=[
                desc.BoolParam(
                    name='useSmartSelection',
                    label='Use Smart Keyframe Selection',
                    description="Use the smart keyframe selection.",
                    value=True,
                    uid=[0]
                ),
                desc.GroupAttribute(
                    name="regularSelection",
                    label="Regular Keyframe Selection",
                    description="Parameters for the regular keyframe selection.\nKeyframes are selected regularly over the sequence with respect to the set parameters.",
                    group=None,  # skip group from command line
                    enabled=lambda node: node.selectionMethod.useSmartSelection.value is False,
                    groupDesc=[
                        desc.IntParam(
                            name="minFrameStep",
                            label="Min Frame Step",
                            description="Minimum number of frames between two keyframes.",
                            value=12,
                            range=(1, 1000, 1),
                            uid=[0],
                            enabled=lambda node: node.regularSelection.enabled
                        ),
                        desc.IntParam(
                            name="maxFrameStep",
                            label="Max Frame Step",
                            description="Maximum number of frames between two keyframes. Ignored if equal to 0.",
                            value=0,
                            range=(0, 1000, 1),
                            uid=[0],
                            enabled=lambda node: node.regularSelection.enabled
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
                            enabled=lambda node: node.regularSelection.enabled
                        ),
                    ],
                ),
                desc.GroupAttribute(
                    name="smartSelection",
                    label="Smart Keyframe Selection",
                    description="Parameters for the smart keyframe selection.\nKeyframes are selected based on their sharpness and optical flow scores.",
                    group=None,  # skip group from command line
                    enabled=lambda node: node.selectionMethod.useSmartSelection.value,
                    groupDesc=[
                        desc.FloatParam(
                            name="pxDisplacement",
                            label="Pixel Displacement",
                            description="The percentage of pixels in the frame that need to have moved since the last keyframe to be considered for the selection",
                            value=3.0,
                            range=(0.0, 100.0, 1.0),
                            uid=[0],
                            enabled=lambda node: node.smartSelection.enabled
                        ),
                        desc.IntParam(
                            name="minNbOutFrames",
                            label="Min Nb Output Frames",
                            description="Minimum number of frames selected to be keyframes.",
                            value=10,
                            range=(1, 100, 1),
                            uid=[0],
                            enabled=lambda node: node.smartSelection.enabled
                        ),
                        desc.IntParam(
                            name="maxNbOutFrames",
                            label="Max Nb Output Frames",
                            description="Maximum number of frames selected to be keyframes.",
                            value=2000,
                            range=(1, 10000, 1),
                            uid=[0],
                            enabled=lambda node: node.smartSelection.enabled
                        ),
                        desc.IntParam(
                            name="rescaledWidth",
                            label="Rescaled Frame's Width",
                            description="Width, in pixels, of the frame after a rescale. Aspect ratio will be preserved. No rescale will be performed if equal to 0.",
                            value=720,
                            range=(0, 4000, 1),
                            uid=[0],
                            enabled=lambda node: node.smartSelection.enabled,
                            advanced=True
                        ),
                        desc.IntParam(
                            name="sharpnessWindowSize",
                            label="Sharpness Window Size",
                            description="The size, in pixels, of the sliding window used to evaluate a frame's sharpness.",
                            value=200,
                            range=(1, 10000, 1),
                            uid=[0],
                            enabled=lambda node: node.smartSelection.enabled,
                            advanced=True
                        ),
                        desc.IntParam(
                            name="flowCellSize",
                            label="Optical Flow Cell Size",
                            description="The size, in pixels, of the cells within a frame in which the optical flow scores is evaluated.",
                            value=90,
                            range=(10, 2000, 1),
                            uid=[0],
                            enabled=lambda node: node.smartSelection.enabled,
                            advanced=True
                        ),
                    ]
                )
            ]
        ),
        desc.GroupAttribute(
            name="debugOptions",
            label="Debug Options",
            description="Debug options for the Smart keyframe selection method.",
            group=None,  # skip group from command line
            enabled=lambda node: node.selectionMethod.useSmartSelection.value,
            advanced=True,
            groupDesc=[
                desc.GroupAttribute(
                    name="debugScores",
                    label="Export Scores",
                    description="Export the computed sharpness and optical flow scores to a file.",
                    group=None,  # skip group from command line
                    enabled=lambda node: node.debugOptions.enabled,
                    groupDesc=[
                        desc.BoolParam(
                            name="exportScores",
                            label="Export Scores To CSV",
                            description="Export the computed sharpness and optical flow scores to a CSV file.",
                            value=False,
                            uid=[0]
                        ),
                        desc.StringParam(
                            name="csvFilename",
                            label="CSV Filename",
                            description="Name of the CSV file to export. It will be written in the node's output folder.",
                            value="scores.csv",
                            uid=[0],
                            enabled=lambda node: node.debugOptions.debugScores.exportScores.value
                        ),
                        desc.BoolParam(
                            name="exportSelectedFrames",
                            label="Export Selected Frames",
                            description="Add a column in the CSV file containing 1s for frames that were selected and 0s for those that were not.",
                            value=False,
                            uid=[0],
                            enabled=lambda node: node.debugOptions.debugScores.exportScores.value
                        )
                    ]
                ),
                desc.GroupAttribute(
                    name="opticalFlowVisualisation",
                    label="Optical Flow Visualisation",
                    description="Visualise the motion vectors for each input frame in HSV.",
                    group=None,  # skip group from command line
                    enabled=lambda node: node.debugOptions.enabled,
                    groupDesc=[
                        desc.BoolParam(
                            name="exportFlowVisualisation",
                            label="Visualise Optical Flow",
                            description="Export each frame's optical flow HSV visualisation as PNG images.",
                            value=False,
                            uid=[0],
                            enabled=lambda node: node.debugOptions.opticalFlowVisualisation.enabled
                        ),
                        desc.BoolParam(
                            name="flowVisualisationOnly",
                            label="Only Visualise Optical Flow",
                            description="Export each frame's optical flow HSV visualisation as PNG images, but do not perform any score computation or frame selection.\n"
                                        "If this option is selected, all the other options will be ignored.",
                            value=False,
                            uid=[0],
                            enabled=lambda node: node.debugOptions.opticalFlowVisualisation.enabled
                        )
                    ]
                ),
                desc.BoolParam(
                    name="skipSelection",
                    label="Skip Frame Selection",
                    description="Compute the sharpness and optical flow scores, but do not proceed to the frame selection.",
                    value=False,
                    uid=[0],
                    enabled=lambda node: node.debugOptions.enabled
                )
            ]
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

