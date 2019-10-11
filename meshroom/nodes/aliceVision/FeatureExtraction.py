__version__ = "1.1"

from meshroom.core import desc


class FeatureExtraction(desc.CommandLineNode):
    commandLine = 'aliceVision_featureExtraction {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=40)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='describerTypes',
            label='Describer Types',
            description='Describer types used to describe an image.',
            value=['sift'],
            values=['akaze', 'akaze_liop', 'akaze_mldb', 'sift', 'sift_float', 'sift_upright', 'akaze_ocv', 'brisk_ocv', 'sift_ocv', 'surf_ocv', 'cctag3', 'cctag4'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.ChoiceParam(
            name='describerPreset',
            label='Describer Preset',
            description='Control the ImageDescriber configuration (low, medium, normal, high, ultra). Configuration "ultra" can take long time !',
            value='normal',
            values=['low', 'medium', 'normal', 'high', 'ultra'],
            exclusive=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='forceCpuExtraction',
            label='Force CPU Extraction',
            description='Use only CPU feature extraction.',
            value=True,
            uid=[],
            advanced=True
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output Folder',
            description='Output path for the features and descriptors files (*.feat, *.desc).',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
