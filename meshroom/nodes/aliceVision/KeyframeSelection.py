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
            name='mediaPaths',
            label='Media Paths',
            description='Input video files or image sequence directories.',
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
                description="Focal in mm (will be use if not 0).",
                value=0.0,
                range=(0.0, 500.0, 1.0),
                uid=[0],
            ),
            name="mmFocals",
            label="mmFocals",
            description="Focals in mm (will be use if not 0)."
        ),
        desc.File(
            name='sensorDbPath',
            label='Sensor Database',
            description='''Camera sensor width database path.''',
            value='${ALICEVISION_SENSOR_DB}',
            uid=[],
        ),
        desc.IntParam(
            name='minFrameStep',
            label='Min Frame Step',
            description='''Minimum number of frames between two keyframes''',
            value=1,
            range=(1, 100, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='maxNbOutFrame',
            label='Max Nb Out Frame',
            description='''Maximum number of output frames (0 = no limit)''',
            value=0,
            range=(0, 10000, 1),
            uid=[0],
        ),
        desc.BoolParam(
            name='useRegularKeyframes',
            label='Use Regular Keyframes',
            description="Disable smart algorithm for frame selection",
            value=False,
            uid=[0],
        ),
        desc.GroupAttribute(
            name="debug",
            label="Debug Parameters",
            description="Debugging options for Keyframe Selection",
            group=None,
            groupDesc=[
                desc.BoolParam(
                    name='computeScores',
                    label='Compute Sharpness And Optical Flow Scores',
                    description='Compute sharpness and optical flow scores on all the input frames, at full resolution.',
                    value=False,
                    uid=[0],
                ),
                desc.BoolParam(
                    name='computeRescaled',
                    label='Compute Scores Of Rescaled Inputs',
                    description='Compute, in additon to the sharpness and optical flow scores on full resolution images, the same scores on rescaled images.',
                    value=True,
                    enabled=lambda node: node.debug.computeScores.value,
                    uid=[],
                ),
                desc.BoolParam(
                    name='flowOnBorders',
                    label='Compute Optical Flow Scores On Image Borders',
                    description='Compute optical flow scores on the top, bottom, left and right borders of all the input frames.',
                    value=False,
                    enabled=lambda node: node.debug.computeScores.value,
                    uid=[0],
                ),
                desc.BoolParam(
                    name='flowByCell',
                    label='Compute Optical Flow Scores Using Cells',
                    description='Compute optical flow scores cell by cell within a frame.',
                    value=False,
                    enabled=lambda node: node.debug.computeScores.value,
                    uid=[0],
                ),
                desc.BoolParam(
                    name='exportSharpness',
                    label='Export Sharpness Scores',
                    description='Export the sharpness score of each frame into a CSV file.',
                    value=True,
                    enabled=lambda node: node.debug.computeScores.value,
                    uid=[],
                ),
                desc.BoolParam(
                    name='exportFlow',
                    label='Export Optical Flow Scores',
                    description='Export the optical flow score of each frame into a CSV file.',
                    value=True,
                    enabled=lambda node: node.debug.computeScores.value,
                    uid=[],
                ),
                desc.BoolParam(
                    name='refineSelection',
                    label='Refine Frame Selection',
                    description='Refine the initial frame selection, which is solely based on optical flow, with sharpness information.',
                    value=True,
                    enabled=lambda node: node.debug.computeScores.value,
                    uid=[],
                ),
                desc.BoolParam(
                    name='noSelection',
                    label='Cancel Keyframe Selection',
                    description='Do not perform the keyframe selection after the score computations.',
                    value=True,
                    enabled=lambda node: node.debug.computeScores.value,
                    uid=[],
                )
        ]),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='Verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name='outputFolder',
            label='Folder',
            description='''Output keyframes folder for extracted frames.''',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
