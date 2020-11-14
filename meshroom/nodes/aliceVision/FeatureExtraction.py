__version__ = "1.1"

from meshroom.core import desc


class FeatureExtraction(desc.CommandLineNode):
    commandLine = 'aliceVision_featureExtraction {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=40)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentation = '''
This node extracts distinctive groups of pixels that are, to some extent, invariant to changing camera viewpoints during image acquisition.
Hence, a feature in the scene should have similar feature descriptions in all images.

This node implements multiple methods:
 * **SIFT**
The most standard method. This is the default and recommended value for all use cases.
 * **AKAZE**
AKAZE can be interesting solution to extract features in challenging condition. It could be able to match wider angle than SIFT but has drawbacks.
It may extract to many features, the repartition is not always good.
It is known to be good on challenging surfaces such as skin.
 * **CCTAG**
CCTag is a marker type with 3 or 4 crowns. You can put markers in the scene during the shooting session to automatically re-orient and re-scale the scene to a known size.
It is robust to motion-blur, depth-of-field, occlusion. Be careful to have enough white margin around your CCTags.


## Online
[https://alicevision.org/#photogrammetry/natural_feature_extraction](https://alicevision.org/#photogrammetry/natural_feature_extraction)
'''

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
            advanced=True,
        ),
        desc.IntParam(
            name='maxThreads',
            label='Max Nb Threads',
            description='Specifies the maximum number of threads to run simultaneously (0 for automatic mode).',
            value=0,
            range=(0, 24, 1),
            uid=[],
            advanced=True,
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
