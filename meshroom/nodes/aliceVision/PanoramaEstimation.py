__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaEstimation(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaEstimation {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Panorama HDR'
    documentation = '''
Estimate relative camera rotations between input images.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="SfM Data File",
            value='',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name='featuresFolder',
                label='Features Folder',
                description="",
                value='',
                uid=[0],
            ),
            name='featuresFolders',
            label='Features Folders',
            description="Folder(s) containing the extracted features."
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name='matchesFolder',
                label='Matches Folder',
                description="",
                value='',
                uid=[0],
            ),
            name='matchesFolders',
            label='Matches Folders',
            description="Folder(s) in which computed matches are stored."
        ),
        desc.ChoiceParam(
            name='describerTypes',
            label='Describer Types',
            description='Describer types used to describe an image.',
            value=['sift'],
            values=['sift', 'sift_float', 'sift_upright', 'dspsift', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4',
                    'sift_ocv', 'akaze_ocv'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.FloatParam(
            name='offsetLongitude',
            label='Longitude offset (deg.)',
            description='''Offset to the panorama longitude''',
            value=0.0,
            range=(-180.0, 180.0, 1.0),
            uid=[0],
        ),
        desc.FloatParam(
            name='offsetLatitude',
            label='Latitude offset (deg.)',
            description='''Offset to the panorama latitude''',
            value=0.0,
            range=(-90.0, 90.0, 1.0),
            uid=[0],
        ),
        desc.ChoiceParam(
            name='rotationAveraging',
            label='Rotation Averaging Method',
            description="Method for rotation averaging :\n"
                        " * L1 minimization\n"
                        " * L2 minimization\n",
            values=['L1_minimization', 'L2_minimization'],
            value='L2_minimization',
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='relativeRotation',
            label='Relative Rotation Method',
            description="Method for relative rotation :\n"
                        " * from essential matrix\n"
                        " * from homography matrix\n"
                        " * from rotation matrix",
            values=['essential_matrix', 'homography_matrix', 'rotation_matrix'],
            value='rotation_matrix',
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='rotationAveragingWeighting',
            label='Rotation Averaging Weighting',
            description='Rotation averaging weighting based on the number of feature matches.',
            value=True,
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='filterMatches',
            label='Filter Matches',
            description='Filter Matches',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='refine',
            label='Refine',
            description='Refine camera relative poses, points and optionally internal camera parameter',
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='lockAllIntrinsics',
            label='Force Lock of All Intrinsics',
            description='Force to keep constant all the intrinsics parameters of the cameras (focal length, \n'
                        'principal point, distortion if any) during the reconstruction.\n'
                        'This may be helpful if the input cameras are already fully calibrated.',
            value=False,
            uid=[0],
        ),
        desc.FloatParam(
            name='maxAngleToPrior',
            label='Max Angle To Priors (deg.)',
            description='''Maximal angle allowed regarding the input prior (in degrees).''',
            value=20.0,
            range=(0.0, 360.0, 1.0),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='maxAngularError',
            label='Max Angular Error (deg.)',
            description='''Maximal angular error in global rotation averging (in degrees).''',
            value=100.0,
            range=(0.0, 360.0, 1.0),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='intermediateRefineWithFocal',
            label='Intermediate Refine: Focal',
            description='Intermediate refine with rotation and focal length only.',
            value=False,
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='intermediateRefineWithFocalDist',
            label='Intermediate Refine: Focal And Distortion',
            description='Intermediate refine with rotation, focal length and distortion.',
            value=False,
            uid=[0],
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
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output SfMData File',
            description='Path to the output sfmdata file',
            value=desc.Node.internalFolder + 'panorama.abc',
            uid=[],
        ),
        desc.File(
            name='outputViewsAndPoses',
            label='Output Poses',
            description='''Path to the output sfmdata file with cameras (views and poses).''',
            value=desc.Node.internalFolder + 'cameras.sfm',
            uid=[],
        ),
    ]
