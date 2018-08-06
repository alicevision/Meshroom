__version__ = "2.0"

from meshroom.core import desc


class ExportAnimatedCamera(desc.CommandLineNode):
    commandLine = 'aliceVision_exportAnimatedCamera {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description='SfMData file containing a complete SfM.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='viewFilter',
            label='SfMData Filter',
            description='A SfMData file use as filter.',
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='exportUndistortedImages',
            label='Export Undistorted Images',
            description='Export Undistorted Images.',
            value=True,
            uid=[0],
        ),
       desc.ChoiceParam(
            name='undistortedImageType',
            label='Undistort Image Format',
            description='Image file format to use for undistorted images ("jpg", "png", "tif", "exr (half)").',
            value='jpg',
            values=['jpg', 'png', 'tif', 'exr'],
            exclusive=True,
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
            label='Output filepath',
            description='Output filepath for the alembic animated camera.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='outputCamera',
            label='Output Camera Filepath',
            description='Output filename for the alembic animated camera.',
            value=desc.Node.internalFolder + 'camera.abc',
            group='',  # exclude from command line
            uid=[],
        ),
    ]
