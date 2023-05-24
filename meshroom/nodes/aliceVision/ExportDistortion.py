__version__ = "1.0"

from meshroom.core import desc

class ExportDistortion(desc.AVCommandLineNode):
    commandLine = 'aliceVision_exportDistortion {allParams}'

    category = 'Export'
    documentation = '''
Export the distortion model and parameters of cameras in a SfM scene.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Folder',
            description='Output folder.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='distoStMap',
            label='Distortion ST Map',
            description='Calibrated distortion ST map.',
            semantic='image',
            value=desc.Node.internalFolder + '<INTRINSIC_ID>_distort.exr',
            group='',  # do not export on the command line
            uid=[],
        ),
        desc.File(
            name='undistoStMap',
            label='Undistortion ST Map',
            description='Calibrated undistortion ST map.',
            semantic='image',
            value=desc.Node.internalFolder + '<INTRINSIC_ID>_undistort.exr',
            group='',  # do not export on the command line
            uid=[],
        ),
    ]
