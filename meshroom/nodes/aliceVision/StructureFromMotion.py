__version__ = "2.0"

import json
import os

from meshroom.core import desc


class StructureFromMotion(desc.CommandLineNode):
    commandLine = 'aliceVision_incrementalSfM {allParams}'
    size = desc.DynamicNodeSize('input')

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
        desc.ListAttribute(
            elementDesc=desc.File(
                name="matchesFolder",
                label="Matches Folder",
                description="",
                value="",
                uid=[0],
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which computed matches are stored."
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
            name='localizerEstimator',
            label='Localizer Estimator',
            description='Estimator type used to localize cameras (acransac, ransac, lsmeds, loransac, maxconsensus).',
            value='acransac',
            values=['acransac', 'ransac', 'lsmeds', 'loransac', 'maxconsensus'],
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='observationConstraint',
            label='Observation Constraint',
            description='Observation contraint mode used in the optimization:\n'
                        ' * Basic: Use standard reprojection error in pixel coordinates\n'
                        ' * Scale: Use reprojection error in pixel coordinates but relative to the feature scale',
            value='Basic',
            values=['Basic', 'Scale'],
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='localizerEstimatorMaxIterations',
            label='Localizer Max Ransac Iterations',
            description='Maximum number of iterations allowed in ransac step.',
            value=4096,
            range=(1, 20000, 1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='localizerEstimatorError',
            label='Localizer Max Ransac Error',
            description='Maximum error (in pixels) allowed for camera localization (resectioning).\n'
                        'If set to 0, it will select a threshold according to the localizer estimator used\n'
                        '(if ACRansac, it will analyze the input data to select the optimal value).',
            value=0.0,
            range=(0.0, 100.0, 0.1),
            uid=[0],
            advanced=True,
        ),
       desc.BoolParam(
            name='lockScenePreviouslyReconstructed',
            label='Lock Scene Previously Reconstructed',
            description='This option is useful for SfM augmentation. Lock previously reconstructed poses and intrinsics.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='useLocalBA',
            label='Local Bundle Adjustment',
            description='It reduces the reconstruction time, especially for large datasets (500+ images),\n'
                        'by avoiding computation of the Bundle Adjustment on areas that are not changing.',
            value=True,
            uid=[0],
        ),
        desc.IntParam(
            name='localBAGraphDistance',
            label='LocalBA Graph Distance',
            description='Graph-distance limit to define the Active region in the Local Bundle Adjustment strategy.',
            value=1,
            range=(2, 10, 1),
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='maxNumberOfMatches',
            label='Maximum Number of Matches',
            description='Maximum number of matches per image pair (and per feature type). \n'
                        'This can be useful to have a quick reconstruction overview. \n'
                        '0 means no limit.',
            value=0,
            range=(0, 50000, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='minNumberOfMatches',
            label='Minimum Number of Matches',
            description='Minimum number of matches per image pair (and per feature type). \n'
                        'This can be useful to have a meaningful reconstruction with accurate keypoints. 0 means no limit.',
            value=0,
            range=(0, 50000, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='minInputTrackLength',
            label='Min Input Track Length',
            description='Minimum track length in input of SfM',
            value=2,
            range=(2, 10, 1),
            uid=[0],
        ),
        desc.IntParam(
            name='minNumberOfObservationsForTriangulation',
            label='Min Observation For Triangulation',
            description='Minimum number of observations to triangulate a point.\n'
                        'Set it to 3 (or more) reduces drastically the noise in the point cloud,\n'
                        'but the number of final poses is a little bit reduced\n'
                        '(from 1.5% to 11% on the tested datasets).',
            value=2,
            range=(2, 10, 1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='minAngleForTriangulation',
            label='Min Angle For Triangulation',
            description='Minimum angle for triangulation.',
            value=3.0,
            range=(0.1, 10, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='minAngleForLandmark',
            label='Min Angle For Landmark',
            description='Minimum angle for landmark.',
            value=2.0,
            range=(0.1, 10, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='maxReprojectionError',
            label='Max Reprojection Error',
            description='Maximum reprojection error.',
            value=4.0,
            range=(0.1, 10, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='minAngleInitialPair',
            label='Min Angle Initial Pair',
            description='Minimum angle for the initial pair.',
            value=5.0,
            range=(0.1, 10, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='maxAngleInitialPair',
            label='Max Angle Initial Pair',
            description='Maximum angle for the initial pair.',
            value=40.0,
            range=(0.1, 60, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='useOnlyMatchesFromInputFolder',
            label='Use Only Matches From Input Folder',
            description='Use only matches from the input matchesFolder parameter.\n'
                        'Matches folders previously added to the SfMData file will be ignored.',
            value=False,
            uid=[],
            advanced=True,
        ),
        desc.BoolParam(
            name='useRigConstraint',
            label='Use Rig Constraint',
            description='Enable/Disable rig constraint.',
            value=True,
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='lockAllIntrinsics',
            label='Force Lock of All Intrinsic Camera Parameters.',
            description='Force to keep constant all the intrinsics parameters of the cameras (focal length, \n'
                        'principal point, distortion if any) during the reconstruction.\n'
                        'This may be helpful if the input cameras are already fully calibrated.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='filterTrackForks',
            label='Filter Track Forks',
            description='Enable/Disable the track forks removal. A track contains a fork when incoherent matches \n'
                        'lead to multiple features in the same image for a single track. \n',
            value=True,
            uid=[0],
        ),
        desc.File(
            name='initialPairA',
            label='Initial Pair A',
            description='Filename of the first image (without path).',
            value='',
            uid=[0],
        ),
        desc.File(
            name='initialPairB',
            label='Initial Pair B',
            description='Filename of the second image (without path).',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='interFileExtension',
            label='Inter File Extension',
            description='Extension of the intermediate file export.',
            value='.abc',
            values=('.abc', '.ply'),
            exclusive=True,
            uid=[],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='Verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output SfMData File',
            description='Path to the output sfmdata file',
            value=desc.Node.internalFolder + 'sfm.abc',
            uid=[],
        ),
        desc.File(
            name='outputViewsAndPoses',
            label='Output SfMData File',
            description='''Path to the output sfmdata file with cameras (views and poses).''',
            value=desc.Node.internalFolder + 'cameras.sfm',
            uid=[],
        ),
        desc.File(
            name='extraInfoFolder',
            label='Output Folder',
            description='Folder for intermediate reconstruction files and additional reconstruction information files.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]

    @staticmethod
    def getResults(node):
        """
        Parse SfM result and return views, poses and intrinsics as three dicts with viewId, poseId and intrinsicId as keys.
        """
        reportFile = node.outputViewsAndPoses.value
        if not os.path.exists(reportFile):
            return {}, {}, {}

        with open(reportFile) as jsonFile:
            report = json.load(jsonFile)

        views = dict()
        poses = dict()
        intrinsics = dict()

        for view in report['views']:
            views[view['viewId']] = view

        for pose in report['poses']:
            poses[pose['poseId']] = pose['pose']

        for intrinsic in report['intrinsics']:
            intrinsics[intrinsic['intrinsicId']] = intrinsic

        return views, poses, intrinsics
