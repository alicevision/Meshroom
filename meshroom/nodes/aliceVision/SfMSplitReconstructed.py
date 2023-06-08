__version__ = "1.0"

from meshroom.core import desc


class SfMSplitReconstructed(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmSplitReconstructed {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
    This nodes takes a sfmData file and split it in two
    - One sfmData with the reconstructed views
    - One sfmData with the non reconstructed views
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file .''',
            value='',
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
            name='reconstructedOutput',
            label='Reconstructed SfMData File',
            description='SfMData file with reconstructed cameras',
            value=desc.Node.internalFolder + 'sfmReconstructed.abc',
            uid=[],
        ),
        desc.File(
            name='notReconstructedOutput',
            label='Not Reconstructed SfMData File',
            description='SfMData file with non reconstructed cameras',
            value=desc.Node.internalFolder + 'sfmNonReconstructed.abc',
            uid=[],
        )
    ]
