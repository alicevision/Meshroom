__version__ = "1.0"

from meshroom.core import desc


class SfMTransfer(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_sfmTransfer {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file .''',
            value='',
            uid=[0],
        ),
        desc.File(
            name='reference',
            label='Reference',
            description='''Path to the scene used as the reference to retrieve resolved poses and intrinsics.''',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='method',
            label='Matching Method',
            description="Matching Method:\n"
                " * from_viewid: Align cameras with same view Id\n"
                " * from_filepath: Align cameras with a filepath matching, using 'fileMatchingPattern'\n"
                " * from_metadata: Align cameras with matching metadata, using 'metadataMatchingList'\n",
            value='from_viewid',
            values=['from_viewid', 'from_filepath', 'from_metadata'],
            exclusive=True,
            uid=[0],
        ),
        desc.StringParam(
            name='fileMatchingPattern',
            label='File Matching Pattern',
            description='Matching regular expression for the "from_cameras_filepath" method. '
                        'You should capture specific parts of the filepath with parenthesis to define matching elements.\n'
                        'Some examples of patterns:\n'
                        ' - Match the filename without extension (default value): ".*\/(.*?)\.\w{3}"\n'
                        ' - Match the filename suffix after "_": ".*\/.*(_.*?\.\w{3})"\n'
                        ' - Match the filename prefix before "_": ".*\/(.*?)_.*\.\w{3}"\n',
            value='.*\/(.*?)\.\w{3}',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="metadataMatching",
                label="Metadata",
                description="",
                value="",
                uid=[0],
            ),
            name="metadataMatchingList",
            label="Metadata Matching List",
            description='List of metadata that should match to create the correspondences. If the list is empty, the default value will be used: ["Make", "Model", "Exif:BodySerialNumber", "Exif:LensSerialNumber"].',
        ),
        desc.BoolParam(
            name='transferPoses',
            label='Poses',
            description='Transfer poses.',
            value=True,
            uid=[0]
        ),
        desc.BoolParam(
            name='transferIntrinsics',
            label='Intrinsics',
            description='Transfer cameras intrinsics.',
            value=True,
            uid=[0]
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='SfMData file.',
            value=desc.Node.internalFolder + 'sfmData.abc',
            uid=[],
        ),
    ]
