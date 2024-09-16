__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ExportColoredPointCloud(desc.AVCommandLineNode):
    commandLine = 'aliceVision_exportColoredPointCloud {allParams}'

    category = 'Export'
    documentation = '''
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="SfMData file containing a complete SfM.",
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
            label="Point Cloud Filepath",
            description="Output point cloud with visibilities as SfMData file.",
            value=desc.Node.internalFolder + "pointCloud.abc",
        ),
    ]
