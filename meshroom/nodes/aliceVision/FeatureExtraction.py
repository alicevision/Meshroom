import sys
from meshroom.core import desc


class FeatureExtraction(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_featureExtraction {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='describerTypes',
            label='Describer Types',
            description='''Describer types used to describe an image.''',
            value=['SIFT'],
            values=['SIFT', 'SIFT_FLOAT', 'AKAZE', 'AKAZE_LIOP', 'AKAZE_MLDB', 'CCTAG3', 'CCTAG4', 'SIFT_OCV', 'AKAZE_OCV'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.ChoiceParam(
            name='describerPreset',
            label='Describer Preset',
            description='''Control the ImageDescriber configuration (low, medium, normal, high, ultra). Configuration 'ultra' can take long time !''',
            value='NORMAL',
            values=['LOW', 'MEDIUM', 'NORMAL', 'HIGH', 'ULTRA'],
            exclusive=True,
            uid=[0],
        ),
        desc.StringParam(
            name='upright',
            label='Upright',
            description='''Upright feature.''',
            value='',
            uid=[0],
        ),
        desc.IntParam(
            name='rangeStart',
            label='Range Start',
            description='''Range image index start.''',
            value=-1,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='rangeSize',
            label='Range Size',
            description='''Range size. Log parameters:''',
            value=1,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''Output path for the features and descriptors files (*.feat, *.desc). Optional parameters:''',
            value='{cache}/{nodeType}/{uid0}/',
            uid=[],
        ),
    ]
