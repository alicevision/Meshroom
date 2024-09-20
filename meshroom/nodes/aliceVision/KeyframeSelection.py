__version__ = "5.0"

from meshroom.core import desc
from meshroom.core.utils import EXR_STORAGE_DATA_TYPE, VERBOSE_LEVEL

# List of supported video extensions (provided by OpenImageIO)
videoExts = [".avi", ".mov", ".mp4", ".m4a", ".m4v", ".3gp", ".3g2", ".mj2", ".m4v", ".mpg"]

class KeyframeSelectionNodeSize(desc.DynamicNodeSize):
    def computeSize(self, node):
        inputPathsSize = super(KeyframeSelectionNodeSize, self).computeSize(node)
        s = 0
        finalSize = 0
        defaultParam = self._param

        # Compute the size for each entry in the list of input paths
        for input in node.attribute("inputPaths").value:
            self._param = input.getFullName()
            s = s + super(KeyframeSelectionNodeSize, self).computeSize(node)

        # Retrieve the maximum number of keyframes for the smart selection (which is high by default)
        maxFramesSmart = node.attribute("selectionMethod.smartSelection.maxNbOutFrames").value

        # If the smart selection is enabled and the number of input frames is available (s is not equal to the number of input paths),
        # set the size as the minimum between the number of input frames and maximum number of output keyframes. If the number of
        # input frames is not available, set the size to the maximum number of output keyframes.
        smartSelectionOn = node.attribute("selectionMethod.useSmartSelection").value
        if smartSelectionOn:
            if s != inputPathsSize:
                finalSize = min(s, maxFramesSmart)
            else:
                finalSize = maxFramesSmart

        # If the smart selection is not enabled, the maximum number of output keyframes for the regular mode can be used
        # if and only if it has been set, in the same way as for the smart selection. If the maximum number of frames has
        # not been set, then the size is either the minimum between the maximum number of output keyframes for the smart
        # selection and the number of input frames if it is available, or the maximum number of output keyframes for the
        # smart selection if the number of input frames is not available.
        else:
            maxFrames = node.attribute("selectionMethod.regularSelection.maxNbOutFrames").value
            if maxFrames > 0 and s != inputPathsSize:
                finalSize = min(s, maxFrames)
            elif maxFrames > 0 and s == inputPathsSize:
                finalSize = maxFrames
            elif maxFrames <= 0 and s != inputPathsSize:
                finalSize = min(s, maxFramesSmart)
            else:
                finalSize = maxFramesSmart

        # Reset the param used to compute size to the default one: if the size is computed again,
        # this will prevent having an inputPathsSize that is erroneous
        self._param = defaultParam
        return finalSize


class KeyframeSelection(desc.AVCommandLineNode):
    commandLine = 'aliceVision_keyframeSelection {allParams}'
    size = KeyframeSelectionNodeSize('inputPaths')

    category = 'Utils'
    documentation = '''
Allows to extract keyframes from a video and insert metadata.
It can extract frames from a synchronized multi-cameras rig.

You can extract frames at regular interval by configuring only the min/maxFrameStep.
'''

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="inputPath",
                label="Input Path",
                description="Input path.",
                value="",
            ),
            name="inputPaths",
            label="Input Paths",
            description="Input video files, image sequence directories or SfMData file.",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="brand",
                label="Brand",
                description="Camera brand.",
                value="",
            ),
            name="brands",
            label="Brands",
            description="Camera brands.",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="model",
                label="Model",
                description="Camera model.",
                value="",
            ),
            name="models",
            label="Models",
            description="Camera models.",
        ),
        desc.ListAttribute(
            elementDesc=desc.FloatParam(
                name="mmFocal",
                label="Focal",
                description="Focal in mm (will be used if not 0).",
                value=0.0,
                range=(0.0, 500.0, 1.0),
            ),
            name="mmFocals",
            label="Focals",
            description="Focals in mm (will be used if not 0).",
        ),
        desc.File(
            name="sensorDbPath",
            label="Sensor Database",
            description="Camera sensor width database path.",
            value="${ALICEVISION_SENSOR_DB}",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="masks",
                label="Masks Path",
                description="Directory containing masks to apply to the frames.",
                value="",
            ),
            name="maskPaths",
            label="Masks",
            description="Masks (e.g. segmentation masks) used to exclude some parts of the frames from the score computations\n"
                        "for the smart keyframe selection.",
            enabled=lambda node: node.selectionMethod.useSmartSelection.value,
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
                    name="useSmartSelection",
                    label="Use Smart Keyframe Selection",
                    description="Use the smart keyframe selection.",
                    value=True,
                ),
                desc.GroupAttribute(
                    name="regularSelection",
                    label="Regular Keyframe Selection",
                    description="Parameters for the regular keyframe selection.\n"
                                "Keyframes are selected regularly over the sequence with respect to the set parameters.",
                    group=None,  # skip group from command line
                    enabled=lambda node: node.selectionMethod.useSmartSelection.value is False,
                    groupDesc=[
                        desc.IntParam(
                            name="minFrameStep",
                            label="Min Frame Step",
                            description="Minimum number of frames between two keyframes.",
                            value=12,
                            range=(1, 1000, 1),
                            enabled=lambda node: node.regularSelection.enabled,
                        ),
                        desc.IntParam(
                            name="maxFrameStep",
                            label="Max Frame Step",
                            description="Maximum number of frames between two keyframes. Ignored if equal to 0.",
                            value=0,
                            range=(0, 1000, 1),
                            enabled=lambda node: node.regularSelection.enabled,
                        ),
                        desc.IntParam(
                            name="maxNbOutFrames",
                            label="Max Nb Output Frames",
                            description="Maximum number of output frames (0 = no limit).\n"
                                        "'minFrameStep' and 'maxFrameStep' will always be respected, so combining them with this parameter\n"
                                        "might cause the selection to stop before reaching the end of the input sequence(s).",
                            value=0,
                            range=(0, 10000, 1),
                            enabled=lambda node: node.regularSelection.enabled,
                        ),
                    ],
                ),
                desc.GroupAttribute(
                    name="smartSelection",
                    label="Smart Keyframe Selection",
                    description="Parameters for the smart keyframe selection.\n"
                                "Keyframes are selected based on their sharpness and optical flow scores.",
                    group=None,  # skip group from command line
                    enabled=lambda node: node.selectionMethod.useSmartSelection.value,
                    groupDesc=[
                        desc.FloatParam(
                            name="pxDisplacement",
                            label="Pixel Displacement",
                            description="The percentage of pixels in the frame that need to have moved since the last keyframe to be considered for the selection.",
                            value=10.0,
                            range=(0.0, 100.0, 1.0),
                            enabled=lambda node: node.smartSelection.enabled,
                        ),
                        desc.IntParam(
                            name="minNbOutFrames",
                            label="Min Nb Output Frames",
                            description="Minimum number of frames selected to be keyframes.",
                            value=40,
                            range=(1, 100, 1),
                            enabled=lambda node: node.smartSelection.enabled,
                        ),
                        desc.IntParam(
                            name="maxNbOutFrames",
                            label="Max Nb Output Frames",
                            description="Maximum number of frames selected to be keyframes.",
                            value=2000,
                            range=(1, 10000, 1),
                            enabled=lambda node: node.smartSelection.enabled,
                        ),
                        desc.IntParam(
                            name="rescaledWidthSharpness",
                            label="Rescaled Frame's Width For Sharpness",
                            description="Width, in pixels, of the frame used for the sharpness score computation after a rescale.\n"
                                        "Aspect ratio will be preserved. No rescale will be performed if equal to 0.",
                            value=720,
                            range=(0, 4000, 1),
                            enabled=lambda node: node.smartSelection.enabled,
                            advanced=True,
                        ),
                        desc.IntParam(
                            name="rescaledWidthFlow",
                            label="Rescaled Frame's Width For Motion",
                            description="Width, in pixels, of the frame used for the motion score computation after a rescale.\n"
                                        "Aspect ratio will be preserved. No rescale will be performed if equal to 0.",
                            value=720,
                            range=(0, 4000, 1),
                            enabled=lambda node: node.smartSelection.enabled,
                            advanced=True,
                        ),
                        desc.IntParam(
                            name="sharpnessWindowSize",
                            label="Sharpness Window Size",
                            description="The size, in pixels, of the sliding window used to evaluate a frame's sharpness.",
                            value=200,
                            range=(1, 10000, 1),
                            enabled=lambda node: node.smartSelection.enabled,
                            advanced=True,
                        ),
                        desc.IntParam(
                            name="flowCellSize",
                            label="Optical Flow Cell Size",
                            description="The size, in pixels, of the cells within a frame in which the optical flow scores is evaluated.",
                            value=90,
                            range=(10, 2000, 1),
                            enabled=lambda node: node.smartSelection.enabled,
                            advanced=True,
                        ),
                        desc.IntParam(
                            name="minBlockSize",
                            label="Multi-Threading Minimum Block Size",
                            description="The minimum number of frames to process for a thread to be spawned.\n"
                                        "If using all the available threads implies processing less than this value in every thread, then less threads should be spawned,\n"
                                        "and each will process at least 'minBlockSize' (except maybe for the very last thread, that might process less).",
                            value=10,
                            range=(1, 1000, 1),
                            invalidate=False,
                            enabled=lambda node: node.smartSelection.enabled,
                            advanced=True,
                        ),
                    ],
                ),
            ],
        ),
        desc.BoolParam(
            name="renameKeyframes",
            label="Rename Output Keyframes",
            description="Instead of using the selected keyframes' index as their name, name them as consecutive output frames.\n"
                        "If the selected keyframes are at index [15, 294, 825], they will be written as [00000.exr, 00001.exr, 00002.exr] with this\n"
                        "option enabled instead of [00015.exr, 00294.exr, 00825.exr].",
            value=False,
            enabled=lambda node: node.outputExtension.value != "none",
        ),
        desc.ChoiceParam(
            name="outputExtension",
            label="Keyframes File Extension",
            description="File extension of the written keyframes.\n"
                        "If 'none' is selected, no keyframe will be written on disk.\n"
                        "For input videos, 'none' should not be used since the written keyframes are used to generate the output SfMData file.",
            value="none",
            values=["none", "exr", "jpg", "png"],
            validValue=lambda node: not (any(ext in input.value.lower() for ext in videoExts for input in node.inputPaths.value) and node.outputExtension.value == "none"),
            errorMessage="A video input has been provided. The output extension should be different from 'none'.",
        ),
        desc.ChoiceParam(
            name="storageDataType",
            label="EXR Storage Data Type",
            description="Storage image data type for keyframes written to EXR files:\n"
                        " - float: Use full floating point (32 bits per channel).\n"
                        " - half: Use half float (16 bits per channel).\n"
                        " - halfFinite: Use half float, but clamp values to avoid non-finite values.\n"
                        " - auto: Use half float if all values can fit, else use full float.",
            values=EXR_STORAGE_DATA_TYPE,
            value="float",
            enabled=lambda node: node.outputExtension.value == "exr",
            advanced=True,
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
                        ),
                        desc.StringParam(
                            name="csvFilename",
                            label="CSV Filename",
                            description="Name of the CSV file to export. It will be written in the node's output folder.",
                            value="scores.csv",
                            enabled=lambda node: node.debugOptions.debugScores.exportScores.value,
                        ),
                        desc.BoolParam(
                            name="exportSelectedFrames",
                            label="Export Selected Frames",
                            description="Add a column in the CSV file containing 1s for frames that were selected and 0s for those that were not.",
                            value=False,
                            enabled=lambda node: node.debugOptions.debugScores.exportScores.value,
                        ),
                    ],
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
                            enabled=lambda node: node.debugOptions.opticalFlowVisualisation.enabled,
                        ),
                        desc.BoolParam(
                            name="flowVisualisationOnly",
                            label="Only Visualise Optical Flow",
                            description="Export each frame's optical flow HSV visualisation as PNG images, but do not perform any score computation or frame selection.\n"
                                        "If this option is selected, all the other options will be ignored.",
                            value=False,
                            enabled=lambda node: node.debugOptions.opticalFlowVisualisation.enabled,
                        ),
                    ],
                ),
                desc.BoolParam(
                    name="skipSharpnessComputation",
                    label="Skip Sharpness Computation",
                    description="Skip the sharpness score computation. A fixed score of 1.0 will be applied by default to all the frames.",
                    value=False,
                    enabled=lambda node: node.debugOptions.enabled,
                ),
                desc.BoolParam(
                    name="skipSelection",
                    label="Skip Frame Selection",
                    description="Compute the sharpness and optical flow scores, but do not proceed to the frame selection.",
                    value=False,
                    enabled=lambda node: node.debugOptions.enabled,
                ),
            ],
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
            name="outputFolder",
            label="Folder",
            description="Output keyframes folder for extracted frames.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="outputSfMDataKeyframes",
            label="Keyframes SfMData",
            description="Output SfMData file containing all the selected keyframes.",
            value=desc.Node.internalFolder + "keyframes.sfm",
        ),
        desc.File(
            name="outputSfMDataFrames",
            label="Frames SfMData",
            description="Output SfMData file containing all the frames that were not selected as keyframes.\n"
                        "If the input contains videos, this file will not be written since all the frames that were not selected do not actually exist on disk.",
            value=desc.Node.internalFolder + "frames.sfm",
        ),
    ]

