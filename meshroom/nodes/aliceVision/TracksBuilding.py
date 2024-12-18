__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class TracksBuilding(desc.AVCommandLineNode):
    commandLine = 'aliceVision_tracksBuilding {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Sparse Reconstruction'
    documentation = '''
It fuses all feature matches between image pairs into tracks. Each track represents a candidate point in space, visible from multiple cameras.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
            exposed=True,
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
            exposed=True,
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="matchesFolder",
                label="Matches Folder",
                description="Folder containing some matches.",
                value="",
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which computed matches are stored.",
            exposed=True,
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types used to describe an image.",
            values=DESCRIBER_TYPES,
            value=["dspsift"],
            exclusive=False,
            joinChar=",",
            exposed=True,
        ),
        desc.IntParam(
            name="minInputTrackLength",
            label="Min Input Track Length",
            description="Minimum track length.",
            value=2,
            range=(2, 10, 1),
        ),
        desc.BoolParam(
            name="useOnlyMatchesFromInputFolder",
            label="Use Only Matches From Input Folder",
            description="Use only matches from the input 'matchesFolder' parameter.\n"
                        "Matches folders previously added to the SfMData file will be ignored.",
            value=False,
            invalidate=False,
            advanced=True,
        ),
        desc.BoolParam(
            name="filterTrackForks",
            label="Filter Track Forks",
            description="Enable/Disable the track forks removal. A track contains a fork when incoherent matches\n"
                        "lead to multiple features in the same image for a single track.",
            value=False,
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
            label="Tracks",
            description="Path to the output tracks file.",
            value=desc.Node.internalFolder + "tracksFile.json",
        ),
    ]
