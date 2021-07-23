__version__ = "2.0"

import os
from meshroom.core import desc


class KeyframeSelection(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_keyframeSelection {allParams}'

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
        desc.ListAttribute(
            elementDesc=desc.FloatParam(
                name="pxFocal",
                label="pxFocal",
                description="Focal in px (will be use and convert in mm if not 0).",
                value=0.0,
                range=(0.0, 500.0, 1.0),
                uid=[0],
            ),
            name="pxFocals",
            label="pxFocals",
            description="Focals in px (will be use and convert in mm if not 0)."
        ),
        desc.ListAttribute(
            elementDesc=desc.IntParam(
                name="frameOffset",
                label="Frame Offset",
                description="Frame offset.",
                value=0,
                range=(0, 100.0, 1.0),
                uid=[0],
            ),
            name="frameOffsets",
            label="Frame Offsets",
            description="Frame offsets."
        ),
        desc.File(
            name='sensorDbPath',
            label='Sensor Db Path',
            description='''Camera sensor width database path.''',
            value=os.environ.get('ALICEVISION_SENSOR_DB', ''),
            uid=[0],
        ),
        desc.File(
            name='voctreePath',
            label='Voctree Path',
            description='''Vocabulary tree path.''',
            value=os.environ.get('ALICEVISION_VOCTREE', ''),
            uid=[0],
        ),
        desc.BoolParam(
            name='useSparseDistanceSelection',
            label='Use Sparse Distance Selection',
            description='Use sparseDistance selection in order to avoid similar keyframes.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='useSharpnessSelection',
            label='Use Sharpness Selection',
            description='Use frame sharpness score for keyframe selection.',
            value=False,
            uid=[0],
        ),
        desc.FloatParam(
            name='sparseDistMaxScore',
            label='Sparse Distance Max Score',
            description='Maximum number of strong common points between two keyframes.',
            value=100.0,
            range=(1.0, 200.0, 1.0),
            uid=[0],
        ),
        desc.ChoiceParam(
            name='sharpnessPreset',
            label='Sharpness Preset',
            description='Preset for sharpnessSelection : {ultra, high, normal, low, very_low, none}',
            value='normal',
            values=['ultra', 'high', 'normal', 'low', 'very_low', 'none'],
            exclusive=True,
            uid=[0],
        ),
        desc.IntParam(
            name='sharpSubset',
            label='Sharp Subset',
            description='''sharp part of the image (1 = all, 2 = size/2, ...)''',
            value=4,
            range=(1, 100, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='minFrameStep',
            label='Min Frame Step',
            description='''minimum number of frames between two keyframes''',
            value=1,
            range=(1, 100, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='maxFrameStep',
            label='Max Frame Step',
            description='''maximum number of frames after which a keyframe can be taken''',
            value=2,
            range=(2, 1000, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='maxNbOutFrame',
            label='Max Nb Out Frame',
            description='''maximum number of output frames (0 = no limit)''',
            value=0,
            range=(0, 10000, 1),
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='outputFolder',
            label='Output Folder',
            description='''Output keyframes folder for extracted frames.''',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]

