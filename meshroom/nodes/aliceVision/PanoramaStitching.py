__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaStitching(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaStitching {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="SfM Data File",
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='outputFileType',
            label='Output File Type',
            description='Output file type for the undistorted images.',
            value='exr',
            values=['jpg', 'png', 'tif', 'exr'],
            exclusive=True,
            uid=[0],
            group='', # not part of allParams, as this is not a parameter for the command line
        ),
        desc.FloatParam(
            name='scaleFactor',
            label='Scale Factor',
            description='Scale factor to resize the output resolution (e.g. 0.5 for downscaling to half resolution).',
            value=0.2,
            range=(0.0, 2.0, 0.1),
            uid=[0],
        ),
        desc.BoolParam(
             name='fisheyeMasking',
             label='Enable Fisheye Masking',
             description='For fisheye images, skip the invalid pixels on the borders.',
             value=False,
             uid=[0],
         ),
         desc.FloatParam(
             name='fisheyeMaskingMargin',
             label='Fisheye Masking Margin',
             description='Margin for fisheye images.',
             value=0.05,
             range=(0.0, 0.5, 0.01),
             uid=[0],
         ),
         desc.FloatParam(
             name='transitionSize',
             label='Transition Size',
             description='Size of the transition between images (in pixels).',
             value=10.0,
             range=(0.0, 100.0, 1.0),
             uid=[0],
         ),
         desc.IntParam(
             name='maxNbImages',
             label='Max Nb Images',
             description='Max number of images to merge.',
             value=0,
             range=(0, 80, 1),
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
            label='Output Panorama',
            description='',
            value=desc.Node.internalFolder + 'panorama.{outputFileTypeValue}',
            uid=[],
        ),
    ]
