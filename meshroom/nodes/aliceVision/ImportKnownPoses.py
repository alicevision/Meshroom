__version__ = "1.0"

from meshroom.core import desc


class ImportKnownPoses(desc.AVCommandLineNode):
    commandLine = 'aliceVision_importKnownPoses {allParams}'
    size = desc.DynamicNodeSize('sfmData')

    documentation = '''
    Import known poses from various file formats like xmp or json.
    '''

    inputs = [
        desc.File(
            name="sfmData",
            label="SfMData",
            description="Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.File(
            name="knownPosesData",
            label="Known Poses Data",
            description="Known poses data in the JSON or XMP format.",
            value="",
            uid=[0],
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            value="info",
            values=["fatal", "error", "warning", "info", "debug", "trace"],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "/sfmData.abc",
            uid=[],
        ),
    ]

