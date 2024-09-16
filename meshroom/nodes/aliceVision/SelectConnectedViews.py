__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class SelectConnectedViews(desc.AVCommandLineNode):
    commandLine = 'aliceVision_selectConnectedViews {allParams}'

    cpu = desc.Level.NORMAL
    ram = desc.Level.NORMAL

    category = 'Dense Reconstruction'
    documentation = '''
Select Connected Views based on SfM landmarks.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.IntParam(
            name="maxTCams",
            label="Max Nb Neighbour Cameras",
            description="Maximum number of neighbour cameras per image.",
            value=10,
            range=(1, 20, 1),
        ),
        desc.FloatParam(
            name="minViewAngle",
            label="Min View Angle",
            description="Minimum angle between two views (select the neighbouring cameras, select depth planes from epipolar segment point).",
            value=2.0,
            range=(0.0, 10.0, 0.1),
            advanced=True,
        ),
        desc.FloatParam(
            name="maxViewAngle",
            label="Max View Angle",
            description="Maximum angle between two views (select the neighbouring cameras, select depth planes from epipolar segment point).",
            value=70.0,
            range=(10.0, 120.0, 1.0),
            advanced=True,
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
            label="Connected Views",
            description="List of connected views in a text file.",
            value=desc.Node.internalFolder + "connectedViews.txt",
        ),
    ]
