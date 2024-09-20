__version__ = "2.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class NodalSfM(desc.AVCommandLineNode):
    commandLine = 'aliceVision_nodalSfM {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Sparse Reconstruction'
    documentation = '''
A Structure-From-Motion node specifically designed to handle pure rotation camera movements.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="tracksFilename",
            label="Tracks File",
            description="Input tracks file.",
            value="",
        ),
        desc.File(
            name="pairs",
            label="Pairs File",
            description="Information on pairs.",
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
            name="output",
            label="SfMData",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfm.abc",
        ),
    ]
