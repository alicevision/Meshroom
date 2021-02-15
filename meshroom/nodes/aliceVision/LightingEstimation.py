__version__ = "1.0"

from meshroom.core import desc


class LightingEstimation(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_lightingEstimation {allParams}'

    category = 'Utils'

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
        desc.ChoiceParam(
            name='lightingEstimationMode',
            label='Lighting Estimation Mode',
            description='Lighting Estimation Mode.',
            value='global',
            values=['global', 'per_image'],
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='lightingColor',
            label='Lighting Color Mode',
            description='Lighting Color Mode.',
            value='RGB',
            values=['RGB', 'Luminance'],
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='albedoEstimationName',
            label='Albedo Estimation Name',
            description='Albedo estimation method used for light estimation.',
            value='constant',
            values=['constant', 'picture', 'median_filter', 'blur_filter'],
            exclusive=True,
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='albedoEstimationFilterSize',
            label='Albedo Estimation Filter Size',
            description='Albedo filter size for estimation method using filter.',
            value=3,
            range=(0, 100, 1),
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
            label='Output Folder',
            description='Folder for output lighting vector files.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
