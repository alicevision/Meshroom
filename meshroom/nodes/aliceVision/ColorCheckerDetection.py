__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ColorCheckerDetection(desc.AVCommandLineNode):
    commandLine = 'aliceVision_colorCheckerDetection {allParams}'
    size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=40)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentation = '''
(BETA) \\
Performs Macbeth color checker chart detection.

Outputs:
- the detected color charts position and colors
- the associated transform matrix from "theoric" to "measured"
assuming that the "theoric" Macbeth chart corners coordinates are:
(0, 0), (1675, 0), (1675, 1125), (0, 1125)

Dev notes:
- Fisheye/pinhole is not handled
- ColorCheckerViewer is unstable with multiple color chart within a same image
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file input, image filenames or regex(es) on the image file path.\n"
                        "Supported regex: '#' matches a single digit, '@' one or more digits, '?' one character "
                        "and '*' zero or more.",
            value="",
        ),
        desc.IntParam(
            name="maxCount",
            label="Max Count By Image",
            description="Maximum color charts count to detect in a single image.",
            value=1,
            range=(1, 3, 1),
            advanced=True,
        ),
        desc.BoolParam(
            name="debug",
            label="Debug",
            description="If checked, debug data will be generated.",
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
            name="outputData",
            label="Color Checker Data",
            description="Output position and colorimetric data extracted from detected color checkers in the images.",
            value=desc.Node.internalFolder + "/ccheckers.json",
        ),
    ]
