__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class SfMBootStraping(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmBootstraping {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Sparse Reconstruction'
    documentation = '''
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="SfMData file.",
            value="",
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="featuresFolder",
                label="Features Folder",
                description="",
                value="",
                uid=[0],
            ),
            name="featuresFolders",
            label="Features Folders",
            description="Folder(s) containing the extracted features and descriptors.",
        ),
        desc.File(
            name="tracksFilename",
            label="Tracks File",
            description="Tracks file.",
            value="",
            uid=[0],
        ),
        desc.File(
            name="pairs",
            label="Pairs File",
            description="Information on pairs.",
            value="",
            uid=[0],
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types used to describe an image.",
            values=DESCRIBER_TYPES,
            value=["dspsift"],
            exclusive=False,
            uid=[0],
            joinChar=",",
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="SfMData",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfm.json",
            uid=[],
        ),
    ]
