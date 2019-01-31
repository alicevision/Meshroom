__version__ = "1.0"

from meshroom.core import desc


class LightingEstimation(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_lightingEstimation {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
            value='',
            uid=[0],
        ), 
        desc.File(
            name="depthMapsFilterFolder",
            label='Filtered Depth Maps Folder',
            description='Input filtered depth maps folder',
            value='',
            uid=[0],
        ),
        desc.File(
            name='imagesFolder',
            label='Images Folder',
            description='Use images from a specific folder instead of those specify in the SfMData file.\nFilename should be the image uid.',
            value='',
            uid=[0],
        ),
    ]
    
    outputs = [
        desc.File(
            name='output',
            label='Output Folder',
            description='Folder for output lighting vector files.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
