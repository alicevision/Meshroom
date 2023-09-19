__version__ = "1.0"

from meshroom.core import desc

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
            uid=[0],
        ),
        desc.File(
            name="input",
            label="Input",
            description="Input SfMData file, image filenames or regex(es) on the image file path.\n"
                        "Supported regex: '#' matches a single digit, '@' one or more digits, '?' one character and '*' zero or more.",
            value="",
            uid=[0],
        ),
        desc.ChoiceParam(
            name="correctionMethod",
            label="Correction Level",
            description="Level of correction:\n"
                        " - luminance: Ajust luminance level only.\n"
                        " - whiteBalance: Apply white balancing in addition to luminance adjustment.\n"
                        " - full: Full color correction.",
            value="luminance",
            values=["luminance", "whiteBalance", "full", "bypass"],
            exclusive=True,
            uid=[0],
        ),
        desc.BoolParam(
            name="useBestColorCheckerOnly",
            label="Use Best Color Chart Only",
            description="Use only the color chart with the best orientation and size to compute the color correction model.",
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name="keepImageName",
            label="Keep Image Name",
            description="Keep image names if different from the view Ids.",
            value=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name="extension",
            label="Output File Extension",
            description="Output image file extension.",
            value="exr",
            values=["exr", ""],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name="storageDataType",
            label="EXR Storage Data Type",
            description="Storage data type for EXR output:\n"
                        " - float: Use full floating point (32 bits per channel).\n"
                        " - half: Use half float (16 bits per channel).\n"
                        " - halfFinite: Use half float, but clamp values to avoid non-finite values.\n"
                        " - auto: Use half float if all values can fit, else use full float.",
            value="float",
            values=["float", "half", "halfFinite", "auto"],
            exclusive=True,
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
        ),
    ]

    outputs = [
        desc.File(
            name="outSfMData",
            label="SfMData",
            description="Output SfMData.",
            value=lambda attr: (desc.Node.internalFolder + os.path.basename(attr.node.input.value)) if (os.path.splitext(attr.node.input.value)[1] in [".abc", ".sfm"]) else "",
            uid=[],
            group="",  # do not export on the command line
        ),
        desc.File(
            name="output",
            label="Folder",
            description="Output images folder.",
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
