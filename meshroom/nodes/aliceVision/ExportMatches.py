__version__ = "1.1"

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
            invalidate=True,
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types used to describe an image.",
            values=DESCRIBER_TYPES,
            value=["dspsift"],
            exclusive=False,
            invalidate=True,
            joinChar=",",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="featuresFolder",
                label="Features Folder",
                description="Folder containing some extracted features and descriptors.",
                value="",
                invalidate=True,
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
                invalidate=True,
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which computed matches are stored.",
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
            exclusive=True,
            invalidate=False,
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Folder",
            description="Output path for the features and descriptors files (*.feat, *.desc).",
            value=desc.Node.internalFolder,
            invalidate=False,
        ),
    ]
