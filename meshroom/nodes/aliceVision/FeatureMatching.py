__version__ = "2.0"

from meshroom.core import desc


class FeatureMatching(desc.CommandLineNode):
    commandLine = 'aliceVision_featureMatching {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=20)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Sparse Reconstruction'
    documentation = '''
This node performs the matching of all features between the candidate image pairs.

It is performed in 2 steps:

 1/ **Photometric Matches**

It performs the photometric matches between the set of features descriptors from the 2 input images.
For each feature descriptor on the first image, it looks for the 2 closest descriptors in the second image and uses a relative threshold between them.
This assumption kill features on repetitive structure but has proved to be a robust criterion.

 2/ **Geometric Filtering**

It performs a geometric filtering of the photometric match candidates.
It uses the features positions in the images to make a geometric filtering by using epipolar geometry in an outlier detection framework
called RANSAC (RANdom SAmple Consensus). It randomly selects a small set of feature correspondences and compute the fundamental (or essential) matrix,
then it checks the number of features that validates this model and iterate through the RANSAC framework.

## Online
[https://alicevision.org/#photogrammetry/feature_matching](https://alicevision.org/#photogrammetry/feature_matching)
'''

    inputs = [
        desc.File(
            name='input',
            label='SfMData',
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
            label='Image Pairs',
            description='Path to a file which contains the list of image pairs to match.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='describerTypes',
            label='Describer Types',
            description='Describer types used to describe an image.',
            value=['dspsift'],
            values=['sift', 'sift_float', 'sift_upright', 'dspsift', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv', 'tag16h5'],
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
        desc.FloatParam(
            name='knownPosesGeometricErrorMax',
            label='Known Poses Geometric Error Max',
            description='Maximum error (in pixels) allowed for features matching guided by geometric information from known camera poses.\n'
                        'If set to 0 it lets the ACRansac select an optimal value.',
            value=5.0,
            range=(0.0, 100.0, 1.0),
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
            name='crossMatching',
            label='Cross Matching',
            description='Make sure that the matching process is symmetric (same matches for I->J than fo J->I)',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='guidedMatching',
            label='Guided Matching',
            description='the found model to improve the pairwise correspondences.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='matchFromKnownCameraPoses',
            label='Match From Known Camera Poses',
            description='Enable the usage of geometric information from known camera poses to guide the feature matching.\n'
                        'If some cameras have unknown poses (so there is no geometric prior), the standard feature matching will be performed.',
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
            label='Matches Folder',
            description='Path to a folder in which computed matches will be stored.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
