__version__ = "1.0"

from meshroom.core import desc
import os.path


class SfMFilter(desc.AVCommandLineNode):
    commandLine = 'aliceVision_filterSfM {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
This node allows to filter the SfM data.

It filters the landmark observations to allow a limited number of observations.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.IntParam(
            name="maxNbObservationsPerLandmark",
            label="Maximum Nb of Observations per Landmark",
            description="Maximum number of allowed observations per landmark.",
            value=5,
            range=(0, 50000, 1),
            advanced=True,
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Output SfMData file.",
            value=lambda attr: desc.Node.internalFolder + (os.path.splitext(os.path.basename(attr.node.input.value))[0] or "sfmData") + ".abc",
            uid=[],
        ),
    ]
