__version__ = "1.0"

from meshroom.core import desc


class ExportColoredPointCloud(desc.CommandLineNode):
    commandLine = 'aliceVision_exportColoredPointCloud {allParams}'

    category = 'Export'

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description='SfMData file containing a complete SfM.',
            value='',
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
            label='Output Point Cloud Filepath',
            description='Output point cloud with visibilities as SfMData file.',
            value="{cache}/{nodeType}/{uid0}/pointCloud.abc",
            uid=[],
        ),
    ]
