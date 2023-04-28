__version__ = "1.0"

from meshroom.core import desc


class TracksBuilding(desc.AVCommandLineNode):
    commandLine = 'aliceVision_tracksBuilding {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Sparse Reconstruction'
    documentation = '''
It fuses all feature matches between image pairs into tracks. Each track represents a candidate point in space, visible from multiple cameras.
'''

    inputs = [
        desc.File(
            name='input',
            label='SfMData',
            description='SfMData file.',
            value='',
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
            description="Folder(s) containing the extracted features and descriptors."
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="matchesFolder",
                label="Matches Folder",
                description="",
                value="",
                uid=[0],
            ),
            name="matchesFolders",
            label="Matches Folders",
            description="Folder(s) in which computed matches are stored."
        ),
        desc.ChoiceParam(
            name='describerTypes',
            label='Describer Types',
            description='Describer types used to describe an image.',
            value=['dspsift'],
            values=['sift', 'sift_float', 'sift_upright', 'dspsift', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv', 'tag16h5'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.IntParam(
            name='minInputTrackLength',
            label='Min Input Track Length',
            description='Minimum track length',
            value=2,
            range=(2, 10, 1),
            uid=[0],
        ),
        desc.BoolParam(
            name='useOnlyMatchesFromInputFolder',
            label='Use Only Matches From Input Folder',
            description='Use only matches from the input matchesFolder parameter.\n'
                        'Matches folders previously added to the SfMData file will be ignored.',
            value=False,
            uid=[],
            advanced=True,
        ),
        desc.BoolParam(
            name='filterTrackForks',
            label='Filter Track Forks',
            description='Enable/Disable the track forks removal. A track contains a fork when incoherent matches \n'
                        'lead to multiple features in the same image for a single track. \n',
            value=False,
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
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Tracks',
            description='Path to the output tracks file',
            value=desc.Node.internalFolder + 'tracksFile.json',
            uid=[],
        ),
    ]
