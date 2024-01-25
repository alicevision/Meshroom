__version__ = "1.0"

from meshroom.core import desc


class ImportE57(desc.AVCommandLineNode):
    commandLine = 'aliceVision_importe57 {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
Import an e57 file and generate a sfmData
'''

    inputs = [
        desc.ListAttribute(
            elementDesc=desc.File(
                name="inputFile",
                label="e57 File",
                description="Path to a e57 file.",
                value="",
                uid=[0],
            ),
            name="input",
            label="Input Files",
            description="Set of e57 files in the same reference frame."
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            value="info",
            values=["fatal", "error", "warning", "info", "debug", "trace"],
            exclusive=True,
            uid=[],
        ),

        desc.FloatParam(
            name="maxDensity",
            label="Points density",
            description="Make sure no points has no neighboor closer than maxDensity meters",
            value=0.01,
            range=(0.0, 0.2, 0.001),
            uid=[0]
        )
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "sfm.abc",
            uid=[],
        ),
    ]

