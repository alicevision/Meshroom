__version__ = "3.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ImageMasking(desc.AVCommandLineNode):
    commandLine = 'aliceVision_imageMasking {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=40)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentaiton = '''
    '''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.ChoiceParam(
            name="algorithm",
            label="Algorithm",
            description="",
            value="HSV",
            values=["HSV", "AutoGrayscaleThreshold"],
        ),
        desc.GroupAttribute(
            name="hsv",
            label="HSV Parameters",
            description="Values to select:\n"
                        " - Green: default values\n"
                        " - White: Tolerance = 1, minSaturation = 0, maxSaturation = 0.1, minValue = 0.8, maxValue = 1\n"
                        " - Black: Tolerance = 1, minSaturation = 0, maxSaturation = 0.1, minValue = 0, maxValue = 0.2",
            group=None,
            enabled=lambda node: node.algorithm.value == "HSV",
            groupDesc=[
                desc.FloatParam(
                    name="hsvHue",
                    label="Hue",
                    description="Hue value to isolate in [0,1] range.\n"
                                "0 = red, 0.33 = green, 0.66 = blue, 1 = red.",
                    semantic="color/hue",
                    value=0.33,
                    range=(0.0, 1.0, 0.01),
                ),
                desc.FloatParam(
                    name="hsvHueRange",
                    label="Tolerance",
                    description="Tolerance around the hue value to isolate.",
                    value=0.1,
                    range=(0.0, 1.0, 0.01),
                ),
                desc.FloatParam(
                    name="hsvMinSaturation",
                    label="Min Saturation",
                    description="Hue is meaningless if saturation is low. Do not mask pixels below this threshold.",
                    value=0.3,
                    range=(0.0, 1.0, 0.01),
                ),
                desc.FloatParam(
                    name="hsvMaxSaturation",
                    label="Max Saturation",
                    description="Do not mask pixels above this threshold. It might be useful to mask white/black pixels.",
                    value=1.0,
                    range=(0.0, 1.0, 0.01),
                ),
                desc.FloatParam(
                    name="hsvMinValue",
                    label="Min Value",
                    description="Hue is meaningless if the value is low. Do not mask pixels below this threshold.",
                    value=0.3,
                    range=(0.0, 1.0, 0.01),
                ),
                desc.FloatParam(
                    name="hsvMaxValue",
                    label="Max Value",
                    description="Do not mask pixels above this threshold. It might be useful to mask white/black pixels.",
                    value=1.0,
                    range=(0.0, 1.0, 0.01),
                ),
            ],
        ),
        desc.BoolParam(
            name="invert",
            label="Invert",
            description="If selected, the selected area is ignored.\n"
                        "If not, only the selected area is considered.",
            value=True,
        ),
        desc.IntParam(
            name="growRadius",
            label="Grow Radius",
            description="Grow the selected area.\n"
                        "It might be used to fill the holes: then use shrinkRadius to restore the initial coutours.",
            value=0,
            range=(0, 50, 1),
        ),
        desc.IntParam(
            name="shrinkRadius",
            label="Shrink Radius",
            description="Shrink the selected area.",
            value=0,
            range=(0, 50, 1),
        ),
        desc.File(
            name="depthMapFolder",
            label="Depth Mask Folder",
            description="Depth mask folder.",
            value="",
        ),
        desc.StringParam(
            name="depthMapExp",
            label="Depth Mask Expression",
            description="Depth mask expression, like '{inputFolder}/{stem}-depth.{ext}'.",
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
            label="Output",
            description="Output folder.",
            value=desc.Node.internalFolder,
        ),
    ]
