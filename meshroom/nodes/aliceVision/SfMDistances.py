__version__ = "3.0"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class SfMDistances(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmDistances {allParams}'
    size = desc.DynamicNodeSize('input')

    documentation = '''
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file.",
            value="",
            uid=[0],
        ),
        desc.ChoiceParam(
            name="objectType",
            label="Type",
            description="",
            value="landmarks",
            values=["landmarks", "cameras"],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name="landmarksDescriberTypes",
            label="Describer Types",
            description="Describer types used to describe an image (only used when using 'landmarks').",
            values=DESCRIBER_TYPES,
            value=["cctag3"],
            exclusive=False,
            uid=[0],
            joinChar=",",
        ),
        desc.StringParam(
            name="A",
            label="A IDs",
            description="It will display the distances between A and B elements.\n"
                        "This value should be an ID or a list of IDs of landmarks IDs or cameras (UID or filename without extension).\n"
                        "It will list all elements if empty.",
            value="",
            uid=[0],
        ),
        desc.StringParam(
            name="B",
            label="B IDs",
            description="It will display the distances between A and B elements.\n"
                        "This value should be an ID or a list of IDs of landmarks IDs or cameras (UID or filename without extension).\n"
                        "It will list all elements if empty.",
            value="",
            uid=[0],
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
    ]
