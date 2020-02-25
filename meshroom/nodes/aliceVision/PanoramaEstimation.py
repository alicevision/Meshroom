__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaEstimation(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaEstimation {allParams}'
    size = desc.DynamicNodeSize('input')

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
            values=['sift', 'sift_float', 'sift_upright', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4',
                    'sift_ocv', 'akaze_ocv'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.IntParam(
            name='orientation',
            label='Orientation',
            description='Orientation',
            value=0,
            range=(0, 6, 1),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='offsetLongitude',
            label='Longitude offset (deg.)',
            description='''Offset to the panorama longitude''',
            value=0.0,
            range=(-180.0, 180.0, 1.0),
            uid=[0],
            advanced=True,
        ),
        desc.FloatParam(
            name='offsetLatitude',
            label='Latitude offset (deg.)',
            description='''Offset to the panorama latitude''',
            value=0.0,
            range=(-90.0, 90.0, 1.0),
            uid=[0],
            advanced=True,
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
            name='refine',
            label='Refine',
            description='Refine camera relative poses, points and optionally internal camera parameter',
            value=True,
            uid=[0],
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
            label='Output Folder',
            description='',
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='outSfMDataFilename',
            label='Output SfMData File',
            description='Path to the output sfmdata file',
            value=desc.Node.internalFolder + 'sfmData.abc',
            uid=[],
        ),
    ]
