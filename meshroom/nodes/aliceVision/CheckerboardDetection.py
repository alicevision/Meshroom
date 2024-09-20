__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class CheckerboardDetection(desc.AVCommandLineNode):
    commandLine = 'aliceVision_checkerboardDetection {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=5)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Other'
    documentation = '''
Detect checkerboard structures in a set of images.
The detection method also supports nested calibration grids.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="Input SfMData file. Viewpoints must correspond to lens calibration grids.",
            value="",
        ),
        desc.BoolParam(
            name="useNestedGrids",
            label="Nested Calibration Grid",
            description="Enable if images contain nested calibration grids. These grids must be centered on the image center.",
            value=False,
        ),
        desc.BoolParam(
            name="doubleSize",
            label="Double Size",
            description="Double the image size prior to processing.",
            value=False,
        ),
        desc.BoolParam(
            name="ignorePixelAspectRatio",
            label="Ignore Pixel Aspect Ratio",
            description="Ignore pixel aspect ratio for detection.",
            value=False,
        ),
        desc.BoolParam(
            name="exportDebugImages",
            label="Export Debug Images",
            description="Export debug images.",
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
            label="Folder",
            description="Output folder.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="checkerLines",
            enabled=lambda node: node.exportDebugImages.value,
            label="Checker Lines",
            description="Debug images.",
            semantic="image",
            value=desc.Node.internalFolder + "<VIEW_ID>.png",
            group="",  # do not export on the command line
        ),
    ]
