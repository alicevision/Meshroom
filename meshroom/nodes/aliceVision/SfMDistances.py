__version__ = "3.0"

from meshroom.core import desc


class SfMDistances(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_sfmDistances {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='objectType',
            label='Type',
            description='',
            value='landmarks',
            values=['landmarks', 'cameras'],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='landmarksDescriberTypes',
            label='Describer Types',
            description='Describer types used to describe an image (only used when using "landmarks").',
            value=['cctag3'],
            values=['sift', 'sift_float', 'sift_upright', 'akaze', 'akaze_liop', 'akaze_mldb', 'cctag3', 'cctag4', 'sift_ocv', 'akaze_ocv'],
            exclusive=False,
            uid=[0],
            joinChar=',',
        ),
        desc.StringParam(
            name='A',
            label='A IDs',
            description='It will display the distances between A and B elements.\n'
                        'This value should be an ID or a list of IDs of landmarks IDs or cameras (UID or filename without extension).\n'
                        'It will list all elements if empty.',
            value='',
            uid=[0],
        ),
        desc.StringParam(
            name='B',
            label='B IDs',
            description='It will display the distances between A and B elements.\n'
                        'This value should be an ID or a list of IDs of landmarks IDs or cameras (UID or filename without extension).\n'
                        'It will list all elements if empty.',
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
    ]
