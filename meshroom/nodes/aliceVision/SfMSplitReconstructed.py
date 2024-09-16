__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class SfMSplitReconstructed(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmSplitReconstructed {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
    This nodes takes a SfMData file as an input and splits it in two output SfMData files:
    - One SfMData containing the reconstructed views
    - One SfMData containing the non-reconstructed views
'''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]

    outputs = [
        desc.File(
            name="reconstructedOutput",
            label="Reconstructed SfMData File",
            description="SfMData file containing the reconstructed cameras.",
            value=desc.Node.internalFolder + "sfmReconstructed.abc",
        ),
        desc.File(
            name="notReconstructedOutput",
            label="Not Reconstructed SfMData File",
            description="SfMData file containing the non-reconstructed cameras.",
            value=desc.Node.internalFolder + "sfmNonReconstructed.abc",
        ),
    ]
