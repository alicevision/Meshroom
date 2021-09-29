__version__ = "2.0"

from meshroom.core import desc


class ConvertSfMFormat(desc.CommandLineNode):
    commandLine = 'aliceVision_convertSfMFormat {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
Convert an SfM scene from one file format to another.
It can also be used to remove specific parts of from an SfM scene (like filter all 3D landmarks or filter 2D observations).
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='fileExt',
            label='SfM File Format',
            description='SfM File Format',
            value='abc',
            values=['abc', 'sfm', 'json', 'ply', 'baf'],
            exclusive=True,
            uid=[0],
            group='',  # exclude from command line
        ),
        desc.ChoiceParam(
            name='describerTypes',
            label='Describer Types',
            description='Describer types to keep.',
            value=['dspsift'],
            values=['sift', 'sift_float', 'sift_upright', 'dspsift', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv', 'tag16h5', 'unknown'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="imageId",
                label="Image id",
                description="",
                value="",
                uid=[0],
            ),
            name="imageWhiteList",
            label="Image White List",
            description='image white list (uids or image paths).',
        ),
        desc.BoolParam(
            name='views',
            label='Views',
            description='Export views.',
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='intrinsics',
            label='Intrinsics',
            description='Export intrinsics.',
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='extrinsics',
            label='Extrinsics',
            description='Export extrinsics.',
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='structure',
            label='Structure',
            description='Export structure.',
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='observations',
            label='Observations',
            description='Export observations.',
            value=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='Path to the output SfM Data file.',
            value=desc.Node.internalFolder + 'sfm.{fileExtValue}',
            uid=[],
            ),
    ]

