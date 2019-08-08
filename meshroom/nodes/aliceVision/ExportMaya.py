__version__ = "1.0"

from meshroom.core import desc


class ExportMaya(desc.CommandLineNode):
    commandLine = 'aliceVision_exportMeshroomMaya {allParams}'

    category = 'Exporters'

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description='',
            value='',
            uid=[0],
        ),
    ]
    
    outputs = [
        desc.File(
            name='output',
            label='Output Folder',
            description='Folder for MeshroomMaya outputs: undistorted images and thumbnails.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
