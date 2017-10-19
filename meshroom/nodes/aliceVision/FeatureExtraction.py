import sys
from meshroom.core import desc


class FeatureExtraction(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_featureExtraction {allParams}'

    input = desc.File(
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    output = desc.File(
            label='Output',
            description='''Output path for the features and descriptors files (*.feat, *.desc). Optional parameters:''',
            value='{cache}/{nodeType}/{uid0}/',
            uid=[],
            isOutput=True,
            )
    describerTypes = desc.ChoiceParam(
            label='Describer Types',
            description='''Describer types used to describe an image.''',
            value=['SIFT'],
            values=['SIFT', 'SIFT_FLOAT', 'AKAZE', 'AKAZE_LIOP', 'AKAZE_MLDB', 'CCTAG3', 'CCTAG4', 'SIFT_OCV', 'AKAZE_OCV'],
            exclusive=False,
            uid=[0],
            joinChar=',',
            )
    describerPreset = desc.ChoiceParam(
            label='Describer Preset',
            description='''Control the ImageDescriber configuration (low, medium, normal, high, ultra). Configuration 'ultra' can take long time !''',
            value='NORMAL',
            values=['low', 'medium', 'normal', 'high', 'ultra'],
            exclusive=True,
            uid=[0],
            )
    upright = desc.StringParam(
            label='Upright',
            description='''Upright feature.''',
            value='',
            uid=[0],
            )
    rangeStart = desc.IntParam(
            label='Range Start',
            description='''Range image index start.''',
            value=-1,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
            )
    rangeSize = desc.IntParam(
            label='Range Size',
            description='''Range size. Log parameters:''',
            value=1,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
            )
    verboseLevel = desc.ChoiceParam(
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
            )
