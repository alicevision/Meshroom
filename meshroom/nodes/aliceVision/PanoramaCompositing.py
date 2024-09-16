__version__ = "2.0"

import json
import os

from meshroom.core import desc
from meshroom.core.utils import EXR_STORAGE_DATA_TYPE, VERBOSE_LEVEL


class PanoramaCompositing(desc.AVCommandLineNode):
    commandLine = 'aliceVision_panoramaCompositing {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=5)
    commandLineRange = '--rangeIteration {rangeIteration} --rangeSize {rangeBlockSize}'
    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Panorama HDR'
    documentation = '''
Once the images have been transformed geometrically (in PanoramaWarping),
they have to be fused together in a single panorama image which looks like a single photography.
The Multi-band Blending method provides the best quality. It averages the pixel values using multiple bands in the frequency domain.
Multiple cameras are contributing to the low frequencies and only the best one contributes to the high frequencies.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="warpingFolder",
            label="Warping Folder",
            description="Panorama warping results folder.",
            value="",
        ),
        desc.File(
            name="labels",
            label="Labels Images",
            description="Panorama seams results images.",
            value="",
        ),
        desc.ChoiceParam(
            name="compositerType",
            label="Compositer Type",
            description="Which compositer should be used to blend images:\n"
                        " - multiband: high quality transition by fusing images by frequency bands.\n"
                        " - replace: debug option with straight transitions.\n"
                        " - alpha: debug option with linear transitions.",
            value="multiband",
            values=["replace", "alpha", "multiband"],
        ),
        desc.IntParam(
            name="forceMinPyramidLevels",
            label="Min Pyramid Levels",
            description="Force the minimal number of levels in the pyramid for multiband compositer.",
            value=0,
            range=(0, 16, 1),
            enabled=lambda node: node.compositerType.value and node.compositerType.value == "multiband",
        ),
        desc.IntParam(
            name="maxThreads",
            label="Max Nb Threads",
            description="Specifies the maximum number of threads to run simultaneously.",
            value=4,
            range=(0, 48, 1),
            invalidate=False,
            advanced=True,
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
                        " - auto: Use half float if all values can fit, else use full float.",
            values=EXR_STORAGE_DATA_TYPE,
            value="float",
        ),
        desc.ChoiceParam(
            name="overlayType",
            label="Overlay Type",
            description="Overlay on top of panorama to analyze transitions:\n"
                        " - none: no overlay.\n"
                        " - borders: display image borders.\n"
                        " - seams: display transitions between images.\n"
                        " - all: display borders and seams.",
            value="none",
            values=["none", "borders", "seams", "all"],
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
            label="Folder",
            description="Output folder containing the composited panorama.",
            value=desc.Node.internalFolder,
        ),
    ]
