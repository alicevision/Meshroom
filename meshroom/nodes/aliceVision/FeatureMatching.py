import sys
from meshroom.core import desc


class FeatureMatching(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_featureMatching {allParams}'

    input = desc.File(
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    output = desc.File(
            label='Output',
            description='''Path to a directory in which computed matches will be stored. Optional parameters:''',
            value='{cache}/{nodeType}/{uid0}/',
            uid=[],
            isOutput=True,
            )
    geometricModel = desc.ChoiceParam(
            label='Geometric Model',
            description='''Pairwise correspondences filtering thanks to robust model estimation: * f: fundamental matrix * e: essential matrix * h: homography matrix''',
            value='f',
            values=['f', 'e', 'h'],
            exclusive=True,
            uid=[0],
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
    featuresDirectory = desc.File(
            label='Features Directory',
            description='''Path to a directory containing the extracted features.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    imagePairsList = desc.File(
            label='Image Pairs List',
            description='''Path to a file which contains the list of image pairs to match.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    photometricMatchingMethod = desc.ChoiceParam(
            label='Photometric Matching Method',
            description='''For Scalar based regions descriptor: * BRUTE_FORCE_L2: L2 BruteForce matching * ANN_L2: L2 Approximate Nearest Neighbor matching * CASCADE_HASHING_L2: L2 Cascade Hashing matching * FAST_CASCADE_HASHING_L2: L2 Cascade Hashing with precomputed hashed regions (faster than CASCADE_HASHING_L2 but use more memory) For Binary based descriptor: * BRUTE_FORCE_HAMMING: BruteForce Hamming matching''',
            value='ANN_L2',
            values=['BRUTE_FORCE_L2', 'ANN_L2', 'CASCADE_HASHING_L2', 'FAST_CASCADE_HASHING_L2', 'BRUTE_FORCE_HAMMING'],
            exclusive=True,
            uid=[0],
            )
    geometricEstimator = desc.ChoiceParam(
            label='Geometric Estimator',
            description='''Geometric estimator: * acransac: A-Contrario Ransac * loransac: LO-Ransac (only available for fundamental matrix)''',
            value='acransac',
            values=['acransac', 'loransac'],
            exclusive=True,
            uid=[0],
            )
    savePutativeMatches = desc.StringParam(
            label='Save Putative Matches',
            description='''putative matches.''',
            value='',
            uid=[0],
            )
    guidedMatching = desc.StringParam(
            label='Guided Matching',
            description='''the found model to improve the pairwise correspondences.''',
            value='',
            uid=[0],
            )
    matchFilePerImage = desc.File(
            label='Match File Per Image',
            description='''matches in a separate file per image.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    distanceRatio = desc.FloatParam(
            label='Distance Ratio',
            description='''Distance ratio to discard non meaningful matches.''',
            value=0.800000012,
            range=(-float('inf'), float('inf'), 0.01),
            uid=[0],
            )
    videoModeMatching = desc.ChoiceParam(
            label='Video Mode Matching',
            description='''sequence matching with an overlap of X images: * 0: will match 0 with (1->X), ... * 2: will match 0 with (1,2), 1 with (2,3), ... * 3: will match 0 with (1,2,3), 1 with (2,3,4), ...''',
            value=0,
            values=['0', '2', '3'],
            exclusive=True,
            uid=[0],
            )
    maxIteration = desc.IntParam(
            label='Max Iteration',
            description='''Maximum number of iterations allowed in ransac step.''',
            value=2048,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
            )
    useGridSort = desc.StringParam(
            label='Use Grid Sort',
            description='''matching grid sort.''',
            value='',
            uid=[0],
            )
    exportDebugFiles = desc.File(
            label='Export Debug Files',
            description='''debug files (svg, dot).''',
            value='',
            uid=[0],
            isOutput=False,
            )
    fileExtension = desc.File(
            label='File Extension',
            description='''File extension to store matches (bin or txt).''',
            value='bin',
            uid=[0],
            isOutput=False,
            )
    maxMatches = desc.IntParam(
            label='Max Matches',
            description='''Maximum number pf matches to keep.''',
            value=0,
            range=(-sys.maxsize, sys.maxsize, 1),
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
            value=0,
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
