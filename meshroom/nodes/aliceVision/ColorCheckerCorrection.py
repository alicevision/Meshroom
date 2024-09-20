__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import EXR_STORAGE_DATA_TYPE, VERBOSE_LEVEL

import os.path


class ColorCheckerCorrection(desc.AVCommandLineNode):
    commandLine = 'aliceVision_colorCheckerCorrection {allParams}'
    size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=40)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentation = '''
(BETA) \\
Performs color calibration from Macbeth color checker chart.

The node assumes all the images to process are sharing the same colorimetric properties.
All the input images will get the same correction.

If multiple color charts are submitted, only the first one will be taken in account.
'''

    inputs = [
        desc.File(
            name="inputData",
            label="Color Checker Data",
            description="Position and colorimetric data of the color checker.",
            value="",
        ),
        desc.File(
            name="input",
            label="Input",
            description="Input SfMData file, image filenames or regex(es) on the image file path.\n"
                        "Supported regex: '#' matches a single digit, '@' one or more digits, '?' one character and "
                        "'*' zero or more.",
            value="",
        ),
        desc.ChoiceParam(
            name="extension",
            label="Output File Extension",
            description="Output image file extension.",
            value="exr",
            values=["exr", ""],
        ),
        desc.ChoiceParam(
            name="storageDataType",
            label="EXR Storage Data Type",
            description="Storage data type for EXR output:\n"
                        " - float: Use full floating point (32 bits per channel).\n"
                        " - half: Use half float (16 bits per channel).\n"
                        " - halfFinite: Use half float, but clamp values to avoid non-finite values.\n"
                        " - auto: Use half float if all values can fit, else use full float.",
            values=EXR_STORAGE_DATA_TYPE,
            value="float",
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
            name="outSfMData",
            label="SfMData",
            description="Output SfMData.",
            value=lambda attr: (desc.Node.internalFolder + os.path.basename(attr.node.input.value)) if (os.path.splitext(attr.node.input.value)[1] in [".abc", ".sfm"]) else "",
            group="",  # do not export on the command line
        ),
        desc.File(
            name="output",
            label="Folder",
            description="Output images folder.",
            value=desc.Node.internalFolder,
        ),
    ]
