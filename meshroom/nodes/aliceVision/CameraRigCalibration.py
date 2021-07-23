__version__ = "1.0"

import os
from meshroom.core import desc


class CameraRigCalibration(desc.CommandLineNode):
    commandLine = 'aliceVision_rigCalibration {allParams}'

    category = 'Utils'

    inputs = [
        desc.File(
            name='sfmdata',
            label='SfM Data',
            description='''The sfmData file.''',
            value='',
            uid=[0],
            ),
        desc.File(
            name='mediapath',
            label='Media Path',
            description='''The path to the video file, the folder of the image sequence or a text file (one image path per line) for each camera of the rig (eg. --mediapath /path/to/cam1.mov /path/to/cam2.mov).''',
            value='',
            uid=[0],
            ),
        desc.File(
            name='cameraIntrinsics',
            label='Camera Intrinsics',
            description='''The intrinsics calibration file for each camera of the rig. (eg. --cameraIntrinsics /path/to/calib1.txt /path/to/calib2.txt).''',
            value='',
            uid=[0],
            ),
        desc.File(
            name='export',
            label='Export',
            description='''Filename for the alembic file containing the rig poses with the 3D points. It also saves a file for each camera named 'filename.cam##.abc'.''',
            value='trackedcameras.abc',
            uid=[0],
            ),
        desc.File(
            name='descriptorPath',
            label='Descriptor Path',
            description='''Folder containing the .desc.''',
            value='',
            uid=[0],
            ),
        desc.ChoiceParam(
            name='matchDescTypes',
            label='Match Describer Types',
            description='''The describer types to use for the matching''',
            value=['dspsift'],
            values=['sift', 'sift_float', 'sift_upright', 'dspsift', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.ChoiceParam(
            name='preset',
            label='Preset',
            description='''Preset for the feature extractor when localizing a new image (low, medium, normal, high, ultra)''',
            value='normal',
            values=['low', 'medium', 'normal', 'high', 'ultra'],
            exclusive=True,
            uid=[0],
            ),
        desc.ChoiceParam(
            name='resectionEstimator',
            label='Resection Estimator',
            description='''The type of *sac framework to use for resection (acransac,loransac)''',
            value='acransac',
            values=['acransac', 'loransac'],
            exclusive=True,
            uid=[0],
            ),
        desc.ChoiceParam(
            name='matchingEstimator',
            label='Matching Estimator',
            description='''The type of *sac framework to use for matching (acransac,loransac)''',
            value='acransac',
            values=['acransac', 'loransac'],
            exclusive=True,
            uid=[0],
            ),
        desc.StringParam(
            name='refineIntrinsics',
            label='Refine Intrinsics',
            description='''Enable/Disable camera intrinsics refinement for each localized image''',
            value='',
            uid=[0],
            ),
        desc.FloatParam(
            name='reprojectionError',
            label='Reprojection Error',
            description='''Maximum reprojection error (in pixels) allowed for resectioning. If set to 0 it lets the ACRansac select an optimal value.''',
            value=4.0,
            range=(0.0, 10.0, 0.1),
            uid=[0],
            ),
        desc.IntParam(
            name='maxInputFrames',
            label='Max Input Frames',
            description='''Maximum number of frames to read in input. 0 means no limit.''',
            value=0,
            range=(0, 1000, 1),
            uid=[0],
            ),
        desc.File(
            name='voctree',
            label='Voctree',
            description='''[voctree] Filename for the vocabulary tree''',
            value=os.environ.get('ALICEVISION_VOCTREE', ''),
            uid=[0],
            ),
        desc.File(
            name='voctreeWeights',
            label='Voctree Weights',
            description='''[voctree] Filename for the vocabulary tree weights''',
            value='',
            uid=[0],
            ),
        desc.ChoiceParam(
            name='algorithm',
            label='Algorithm',
            description='''[voctree] Algorithm type: {FirstBest,AllResults}''',
            value='AllResults',
            values=['FirstBest', 'AllResults'],
            exclusive=True,
            uid=[0],
            ),
        desc.IntParam(
            name='nbImageMatch',
            label='Nb Image Match',
            description='''[voctree] Number of images to retrieve in the database''',
            value=4,
            range=(0, 50, 1),
            uid=[0],
            ),
        desc.IntParam(
            name='maxResults',
            label='Max Results',
            description='''[voctree] For algorithm AllResults, it stops the image matching when this number of matched images is reached. If 0 it is ignored.''',
            value=10,
            range=(0, 100, 1),
            uid=[0],
            ),
        desc.FloatParam(
            name='matchingError',
            label='Matching Error',
            description='''[voctree] Maximum matching error (in pixels) allowed for image matching with geometric verification. If set to 0 it lets the ACRansac select an optimal value.''',
            value=4.0,
            range=(0.0, 10.0, 0.1),
            uid=[0],
            ),
        desc.IntParam(
            name='nNearestKeyFrames',
            label='N Nearest Key Frames',
            description='''[cctag] Number of images to retrieve in database''',
            value=5,
            range=(0, 50, 1),
            uid=[0],
            ),
    ]

    outputs = [
        desc.File(
            name='outfile',
            label='Output File',
            description='''The name of the file where to store the calibration data''',
            value=desc.Node.internalFolder + 'cameraRigCalibration.rigCal',
            uid=[],
            ),
    ]
