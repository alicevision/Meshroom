__version__ = "2.0"

from meshroom.core import desc


class LdrToHdrMerge(desc.CommandLineNode):
    commandLine = 'aliceVision_LdrToHdrMerge {allParams}'
    size = desc.DynamicNodeSize('input')
    #parallelization = desc.Parallelization(blockSize=40)
    #commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentation = '''
    Calibrate LDR to HDR response curve from samples
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='response',
            label='Response file',
            description='Response file',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='fusionWeight',
            label='Fusion Weight',
            description="Weight function used to fuse all LDR images together:\n"
                        " * gaussian \n"
                        " * triangle \n"
                        " * plateau",
            value='gaussian',
            values=['gaussian', 'triangle', 'plateau'],
            exclusive=True,
            uid=[0],
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
            name='outSfMDataFilename',
            label='Output SfMData File',
            description='Path to the output sfmdata file',
            value=desc.Node.internalFolder + 'sfmData.sfm',
            uid=[],
        )
    ]