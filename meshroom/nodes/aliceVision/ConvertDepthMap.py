__version__ = "1.0"

from meshroom.core import desc


class ConvertDepthMap(desc.AVCommandLineNode):
    commandLine = 'aliceVision_convertDepthMap {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=4)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'
    category = 'Dense Reconstruction'
    documentation = '''Convert depth maps files to obj meshes files'''

    inputs = [
        desc.File(
            name='input',
            label='SfMData',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.File(
            name="depthMapsFolder",
            label="DepthMaps Folder",
            description="Input depth maps folder",
            value="",
            uid=[0],
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
            label='Converted DepthMaps Folder',
            description='Output folder for depth maps meshes.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
