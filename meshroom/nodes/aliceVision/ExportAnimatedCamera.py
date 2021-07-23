__version__ = "2.0"

from meshroom.core import desc


class ExportAnimatedCamera(desc.CommandLineNode):
    commandLine = 'aliceVision_exportAnimatedCamera {allParams}'

    category = 'Export'
    documentation = '''
Convert cameras from an SfM scene into an animated cameras in Alembic file format.
Based on the input image filenames, it will recognize the input video sequence to create an animated camera.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description='SfMData file containing a complete SfM.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='sfmDataFilter',
            label='SfMData Filter',
            description='Filter out cameras from the export if they are part of this SfMData. Export all cameras if empty.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='viewFilter',
            label='View Filter',
            description='Select the cameras to export using an expression based on the image filepath. Export all cameras if empty.',
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='exportUVMaps',
            label='Export UV Maps',
            description='Export UV Maps, absolutes values (x,y) of distortion are encoding in  UV channels.',
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='exportUndistortedImages',
            label='Export Undistorted Images',
            description='Export Undistorted Images.',
            value=False,
            uid=[0],
        ),
       desc.ChoiceParam(
            name='undistortedImageType',
            label='Undistort Image Format ',
            description='Image file format to use for undistorted images ("jpg", "png", "tif", "exr (half)").',
            value='exr',
            values=['jpg', 'png', 'tif', 'exr'],
            exclusive=True,
            uid=[0],
            enabled= lambda node: node.exportUndistortedImages.value,
        ),
        desc.BoolParam(
            name='exportFullROD',
            label='Export Full ROD',
            description='Export Full ROD.',
            value=False,
            enabled=lambda node: node.exportUndistortedImages.value and node.undistortedImageType.value == 'exr',
            uid=[0],
        ),
        desc.BoolParam(
            name='correctPrincipalPoint',
            label='Correct Principal Point ',
            description='Correct Principal Point.',
            value=True,
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
        desc.File(
            name='outputUndistorted',
            label='Output Undistorted images Filepath',
            description='Output Undistorted images.',
            value=desc.Node.internalFolder + 'undistort',
            group='',  # exclude from command line
            uid=[],
        ),
        ]

