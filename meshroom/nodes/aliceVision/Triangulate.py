__version__ = "2.0"

from meshroom.core import desc


class Triangulate(desc.AVCommandLineNode):
    commandLine = 'aliceVision_triangulate {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Sparse Reconstruction'
    documentation = '''Perfom keypoint triangulation (as it is done in the SfM)'''

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
            value=['dspsift'],
            values=['sift', 'sift_float', 'sift_upright', 'dspsift', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv', 'tag16h5'],
            exclusive=False,
            uid=[0],
            joinChar=',',
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
            range=(0.1, 10.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='minAngleForLandmark',
            label='Min Angle For Landmark',
            description='Minimum angle for landmark.',
            value=2.0,
            range=(0.1, 10.0, 0.1),
            uid=[0],
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
        desc.IntParam(
            name='rigMinNbCamerasForCalibration',
            label='Min Nb Cameras For Rig Calibration',
            description='Minimal number of cameras to start the calibration of the rig',
            value=20,
            range=(1, 50, 1),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='computeStructureColor',
            label='Compute Structure Color',
            description='Enable/Disable color computation of each 3D point.',
            value=True,
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
            label='SfMData',
            description='Path to the output sfmdata file',
            value=desc.Node.internalFolder + 'sfm.abc',
            uid=[],
        ),
        desc.File(
            name='extraInfoFolder',
            label='Folder',
            description='Folder for intermediate reconstruction files and additional reconstruction information files.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
