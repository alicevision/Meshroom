import sys, os
from meshroom.core import desc


class KeyframeSelection(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_keyframeSelection {allParams}'

    inputs = [
        desc.File(
            name='mediaPaths',
            label='Media Paths',
            description='''Input video files or image sequence directories.''',
            value='',
            uid=[0],
            ),
        desc.IntParam(
            name='maxNbOutFrame',
            label='Max Nb Out Frame',
            description='''maximum number of output frames (0 = no limit)''',
            value=1000,
            range=(0, 10000, 1),
            uid=[],
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
        desc.StringParam(
            name='brands',
            label='Brands',
            description='''Camera brands.''',
            value='',
            uid=[0],
            ),
        desc.StringParam(
            name='models',
            label='Models',
            description='''Camera models.''',
            value='',
            uid=[0],
            ),
        desc.FloatParam(
            name='mmFocals',
            label='Mm Focals',
            description='''Focals in mm (will be use if not 0).''',
            value=0.0,
            range=(0.0, 500.0, 1.0),
            uid=[0],
            ),
        desc.FloatParam(
            name='pxFocals',
            label='Px Focals',
            description='''Focals in px (will be use and convert in mm if not 0).''',
            value=0.0,
            range=(0.0, 500.0, 1.0),
            uid=[0],
            ),
        desc.ChoiceParam(
            name='sharpnessPreset',
            label='Sharpness Preset',
            description='''Preset for sharpnessSelection : {ultra, high, normal, low, very_low, none}''',
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
            value=12,
            range=(1, 100, 1),
            uid=[0],
            ),
        desc.IntParam(
            name='maxFrameStep',
            label='Max Frame Step',
            description='''maximum number of frames after which a keyframe can be taken''',
            value=36,
            range=(2, 1000, 1),
            uid=[0],
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

