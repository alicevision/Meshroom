__version__ = "1.0"

from meshroom.core import desc


class ImportKnownPoses(desc.CommandLineNode):
    commandLine = 'aliceVision_importKnownPoses {allParams}'
    size = desc.DynamicNodeSize('sfmData')

    documentation = '''
    Import known poses from various file formats like xmp or json.
    '''

    inputs = [
        desc.File(
            name='sfmData',
            label='SfmData',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='knownPosesData',
            label='KnownPosesData',
            description='KnownPoses data in the json or xmp format',
            value='',
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='Path to the output smfData file.',
            value=desc.Node.internalFolder + "/sfmData.abc",
            uid=[],
            ),
    ]

