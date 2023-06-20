__version__ = "1.0"

from meshroom.core import desc


class ImageSegmentation(desc.AVCommandLineNode):
    commandLine = 'aliceVision_imageSegmentation {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
    Generate a mask with segmented labels for each pixel
    '''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file input',
            value='',
            uid=[0],
        ),

        desc.File(
            name="modelPath",
            label="Segmentation model path",
            description="Weights file for the internal model",
            value="${ALICEVISION_SEMANTIC_SEGMENTATION_MODEL}",
            uid=[0]
        ),

        desc.ListAttribute(
            elementDesc=desc.StringParam(
                        name='className',
                        label='Class Name',
                        description='Class name to be added to the mask',
                        value='classname',
                        uid=[0]),
            name="validClasses",
            label="Valid classes",
            description="Classes names which are to be considered"
        ),

        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Masks Folder',
            description='Output path for the masks.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]

