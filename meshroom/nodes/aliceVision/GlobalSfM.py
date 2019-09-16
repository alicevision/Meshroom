__version__ = "1.0"

import json
import os

from meshroom.core import desc


class GlobalSfM(desc.CommandLineNode):
    commandLine = 'aliceVision_globalSfM {allParams}'
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
        ),
        desc.ChoiceParam(
            name='translationAveraging',
            label='Translation Averaging Method',
            description="Method for translation averaging :\n"
                        " * L1 minimization\n"
                        " * L2 minimization of sum of squared Chordal distances\n"
                        " * L1 soft minimization",
            values=['L1_minimization', 'L2_minimization', 'L1_soft_minimization'],
            value='L1_soft_minimization',
            exclusive=True,
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
        )
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
            value=desc.Node.internalFolder + 'SfmData.abc',
            uid=[],
        ),
    ]
