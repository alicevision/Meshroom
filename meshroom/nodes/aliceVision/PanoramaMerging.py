__version__ = "1.0"

import json
import os

from meshroom.core import desc
from meshroom.core.utils import EXR_STORAGE_DATA_TYPE, VERBOSE_LEVEL


class PanoramaMerging(desc.AVCommandLineNode):
    commandLine = 'aliceVision_panoramaMerging {allParams}'
    size = desc.DynamicNodeSize('input')
    cpu = desc.Level.NORMAL
    ram = desc.Level.INTENSIVE

    category = 'Panorama HDR'
    documentation = '''
Merge all inputs coming from the PanoramaCompositing node.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="compositingFolder",
            label="Compositing Folder",
            description="Panorama compositing results.",
            value="",
        ),
        desc.ChoiceParam(
            name="outputFileType",
            label="Output File Type",
            description="Output file type for the merged panorama.",
            value="exr",
            values=["jpg", "png", "tif", "exr"],
            group="",  # not part of allParams, as this is not a parameter for the command line
        ),
        desc.BoolParam(
            name="useTiling",
            label="Use Tiling",
            description="Enable tiling mode for parallelization.",
            value=True,
            exposed=True,
        ),
        desc.ChoiceParam(
            name="storageDataType",
            label="Storage Data Type",
            description="Storage image data type:\n"
                        " - float: Use full floating point (32 bits per channel).\n"
                        " - half: Use half float (16 bits per channel).\n"
                        " - halfFinite: Use half float, but clamp values to avoid non-finite values.\n"
                        " - auto: Use half float if all values can fit, else use full float.\n",
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
            name="outputPanorama",
            label="Panorama",
            description="Output merged panorama image.",
            semantic="image",
            value=desc.Node.internalFolder + "panorama.{outputFileTypeValue}",
        ),
    ]
