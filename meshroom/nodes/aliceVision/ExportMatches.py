__version__ = "2.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class ExportMatches(desc.AVCommandLineNode):
    commandLine = 'aliceVision_exportMatches {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Export'
    documentation = '''
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file.",
            value="",
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types used to describe an image.",
            values=DESCRIBER_TYPES,
            value=["dspsift"],
            exclusive=False,
            joinChar=",",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="featuresFolder",
                label="Features Folder",
                description="Folder containing some extracted features and descriptors.",
                value="",
            ),
            name="featuresFolders",
            label="Features Folders",
            description="Folder(s) containing the extracted features and descriptors.",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="matchesFolder",
                label="Matches Folder",
                description="Folder containing some computed matches.",
                value="",
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which computed matches are stored.",
        ),
        desc.File(
            name="filterA",
            label="Filter A",
            description="One item of the pair must match this.",
            value="",
        ),
        desc.File(
            name="filterB",
            label="Filter B",
            description="One item of the pair must match this.",
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
            label="Folder",
            description="Output path for the features and descriptors files (*.feat, *.desc).",
            value=desc.Node.internalFolder,
        ),
    ]
