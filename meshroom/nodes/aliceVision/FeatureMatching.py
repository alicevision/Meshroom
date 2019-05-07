__version__ = "2.0"

from meshroom.core import desc


class FeatureMatching(desc.CommandLineNode):
    commandLine = 'aliceVision_featureMatching {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=20)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="featuresFolder",
                label="Features Folder",
                description="",
                value="",
                uid=[0],
            ),
            name="featuresFolders",
            label="Features Folders",
            description="Folder(s) containing the extracted features and descriptors."
        ),
        desc.File(
            name='imagePairsList',
            label='Image Pairs List',
            description='Path to a file which contains the list of image pairs to match.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='describerTypes',
            label='Describer Types',
            description='Describer types used to describe an image.',
            value=['sift'],
            values=['sift', 'sift_float', 'sift_upright', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.ChoiceParam(
            name='photometricMatchingMethod',
            label='Photometric Matching Method',
            description='For Scalar based regions descriptor\n'
                        ' * BRUTE_FORCE_L2: L2 BruteForce matching\n'
                        ' * ANN_L2: L2 Approximate Nearest Neighbor matching\n'
                        ' * CASCADE_HASHING_L2: L2 Cascade Hashing matching\n'
                        ' * FAST_CASCADE_HASHING_L2: L2 Cascade Hashing with precomputed hashed regions (faster than CASCADE_HASHING_L2 but use more memory) \n'
                        'For Binary based descriptor\n'
                        ' * BRUTE_FORCE_HAMMING: BruteForce Hamming matching',
            value='ANN_L2',
            values=('BRUTE_FORCE_L2', 'ANN_L2', 'CASCADE_HASHING_L2', 'FAST_CASCADE_HASHING_L2', 'BRUTE_FORCE_HAMMING'),
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='geometricEstimator',
            label='Geometric Estimator',
            description='Geometric estimator: (acransac: A-Contrario Ransac, loransac: LO-Ransac (only available for "fundamental_matrix" model)',
            value='acransac',
            values=['acransac', 'loransac'],
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='geometricFilterType',
            label='Geometric Filter Type',
            description='Geometric validation method to filter features matches: \n'
                        ' * fundamental_matrix\n'
                        ' * fundamental_with_distortion\n'
                        ' * essential_matrix\n'
                        ' * homography_matrix\n'
                        ' * homography_growing\n'
                        ' * no_filtering',
            value='fundamental_matrix',
            values=['fundamental_matrix', 'fundamental_with_distortion', 'essential_matrix', 'homography_matrix', 'homography_growing', 'no_filtering'],
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='distanceRatio',
            label='Distance Ratio',
            description='Distance ratio to discard non meaningful matches.',
            value=0.8,
            range=(0.0, 1.0, 0.01),
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='maxIteration',
            label='Max Iteration',
            description='Maximum number of iterations allowed in ransac step.',
            value=2048,
            range=(1, 20000, 1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='geometricError',
            label='Geometric Validation Error',
            description='Maximum error (in pixels) allowed for features matching during geometric verification.\n'
                        'If set to 0, it will select a threshold according to the localizer estimator used\n'
                        '(if ACRansac, it will analyze the input data to select the optimal value).',
            value=0.0,
            range=(0.0, 10.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='maxMatches',
            label='Max Matches',
            description='Maximum number of matches to keep.',
            value=0,
            range=(0, 10000, 1),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='savePutativeMatches',
            label='Save Putative Matches',
            description='putative matches.',
            value=False,
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='guidedMatching',
            label='Guided Matching',
            description='the found model to improve the pairwise correspondences.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='exportDebugFiles',
            label='Export Debug Files',
            description='debug files (svg, dot).',
            value=False,
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
            description='Path to a folder in which computed matches will be stored.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
