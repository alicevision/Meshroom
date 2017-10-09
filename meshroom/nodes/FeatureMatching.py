
from meshroom.core import desc

class FeatureMatching(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'openMVG_main_ComputeMatches {allParams}'

    input_file = desc.FileAttribute(
            label='Input File',
            description='''a SfM_Data file''',
            value='',
            shortName='i',
            arg='',
            uid=[0],
            isOutput=False,
            )
    out_dir = desc.FileAttribute(
            label='Out Dir',
            description='''path to directory in which computed matches will be stored [Optional]''',
            value='{cache}/{nodeType}/{uid0}/',
            shortName='o',
            arg='path',
            uid=[0],
            isOutput=True,
            )
    describerMethods = desc.ParamAttribute(
            label='Describer Methods',
            description='''(methods to use to describe an image): SIFT (default), SIFT_FLOAT to use SIFT stored as float, AKAZE: AKAZE with floating point descriptors, AKAZE_MLDB: AKAZE with binary descriptors use the found model to improve the pairwise correspondences.''',
            value='',
            shortName='m',
            arg='',
            uid=[0],
            isOutput=False,
            )
    featuresDir = desc.FileAttribute(
            label='Features Dir',
            description='''Path to directory containing the extracted features (default: $out_dir)''',
            value='',
            shortName='F',
            arg='',
            uid=[0],
            isOutput=False,
            )
    save_putative_matches = desc.ParamAttribute(
            label='Save Putative Matches',
            description='''Save putative matches''',
            value='',
            shortName='p',
            arg='',
            uid=[0],
            isOutput=False,
            )
    ratio = desc.ParamAttribute(
            label='Ratio',
            description='''Distance ratio to discard non meaningful matches 0.8: (default).''',
            value='',
            shortName='r',
            arg='',
            uid=[0],
            isOutput=False,
            )
    geometric_model = desc.ParamAttribute(
            label='Geometric Model',
            description='''(pairwise correspondences filtering thanks to robust model estimation): f: (default) fundamental matrix, e: essential matrix, h: homography matrix.''',
            value='',
            shortName='g',
            arg='',
            uid=[0],
            isOutput=False,
            )
    video_mode_matching = desc.ParamAttribute(
            label='Video Mode Matching',
            description='''(sequence matching with an overlap of X images) X: with match 0 with (1->X), ...] 2: will match 0 with (1,2), 1 with (2,3), ... 3: will match 0 with (1,2,3), 1 with (2,3,4), ...''',
            value='',
            shortName='v',
            arg='',
            uid=[0],
            isOutput=False,
            )
    pair_list = desc.FileAttribute(
            label='Pair List',
            description='''filepath A file which contains the list of matches to perform.''',
            value='',
            shortName='l',
            arg='',
            uid=[0],
            isOutput=False,
            )
    range_start = desc.ParamAttribute(
            label='Range Start',
            description='''range image index start To compute only the matches for specified range. This allows to compute different matches on different computers in parallel.''',
            value='',
            shortName='s',
            arg='',
            uid=[0],
            isOutput=False,
            )
    range_size = desc.ParamAttribute(
            label='Range Size',
            description='''range size To compute only the matches for specified range. This allows to compute different matches on different computers in parallel.''',
            value='',
            shortName='d',
            arg='',
            uid=[0],
            isOutput=False,
            )
    nearest_matching_method = desc.ParamAttribute(
            label='Nearest Matching Method',
            description='''For Scalar based regions descriptor: BRUTE_FORCE_L2: L2 BruteForce matching, ANN_L2: L2 Approximate Nearest Neighbor matching (default), CASCADE_HASHING_L2: L2 Cascade Hashing matching. FAST_CASCADE_HASHING_L2: L2 Cascade Hashing with precomputed hashed regions (faster than CASCADE_HASHING_L2 but use more memory). For Binary based descriptor: BRUTE_FORCE_HAMMING: BruteForce Hamming matching.''',
            value='',
            shortName='n',
            arg='',
            uid=[0],
            isOutput=False,
            )
    geometricEstimator = desc.ParamAttribute(
            label='Geometric Estimator',
            description='''Geometric estimator acransac: A-Contrario Ransac (default), loransac: LO-Ransac (only available for fundamental matrix)''',
            value='',
            shortName='G',
            arg='',
            uid=[0],
            isOutput=False,
            )
    guided_matching = desc.ParamAttribute(
            label='Guided Matching',
            description='''use the found model to improve the pairwise correspondences.''',
            value='',
            shortName='M',
            arg='',
            uid=[0],
            isOutput=False,
            )
    max_iteration = desc.ParamAttribute(
            label='Max Iteration',
            description='''number of maximum iterations allowed in ransac step.''',
            value='',
            shortName='I',
            arg='',
            uid=[0],
            isOutput=False,
            )
    match_file_per_image = desc.FileAttribute(
            label='Match File Per Image',
            description='''Save matches in a separate file per image''',
            value='',
            shortName='x',
            arg='',
            uid=[0],
            isOutput=False,
            )
    max_matches = desc.ParamAttribute(
            label='Max Matches',
            description='''''',
            value='',
            shortName='u',
            arg='',
            uid=[0],
            isOutput=False,
            )
    use_grid_sort = desc.ParamAttribute(
            label='Use Grid Sort',
            description='''Use matching grid sort''',
            value='',
            shortName='y',
            arg='',
            uid=[0],
            isOutput=False,
            )
    export_debug_files = desc.FileAttribute(
            label='Export Debug Files',
            description='''Export debug files (svg, dot)''',
            value='',
            shortName='e',
            arg='',
            uid=[0],
            isOutput=False,
            )
    fileExtension = desc.FileAttribute(
            label='File Extension',
            description='''File extension to store matches: bin (default), txt Unrecognized option --help''',
            value='',
            shortName='t',
            arg='',
            uid=[0],
            isOutput=False,
            )