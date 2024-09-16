__version__ = "1.2"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ImageSegmentation(desc.AVCommandLineNode):
    commandLine = 'aliceVision_imageSegmentation {allParams}'
    size = desc.DynamicNodeSize('input')
    gpu = desc.Level.INTENSIVE
    parallelization = desc.Parallelization(blockSize=50)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Utils'
    documentation = '''
Generate a mask with segmented labels for each pixel.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file input.",
            value="",
        ),
        desc.File(
            name="modelPath",
            label="Segmentation Model",
            description="Weights file for the internal model.",
            value="${ALICEVISION_SEMANTIC_SEGMENTATION_MODEL}",
        ),
        desc.ChoiceParam(
            name="validClasses",
            label="Classes",
            description="Classes names which are to be considered.",
            value=["person"],
            values=[
                "__background__",
                "aeroplane",
                "bicycle", "bird", "boat", "bottle", "bus",
                "car", "cat", "chair", "cow",
                "diningtable", "dog",
                "horse",
                "motorbike",
                "person", "pottedplant",
                "sheep", "sofa",
                "train", "tvmonitor"
            ],
            exclusive=False,
        ),
        desc.BoolParam(
            name="maskInvert",
            label="Invert Masks",
            description="Invert mask values. If selected, the pixels corresponding to the mask will be set to 0 instead of 255.",
            value=False,
        ),
        desc.BoolParam(
            name="useGpu",
            label="Use GPU",
            description="Use GPU for computation if available",
            value=True,
            invalidate=False,
        ),
        desc.BoolParam(
            name="keepFilename",
            label="Keep Filename",
            description="Keep Input Filename",
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
            label="Masks Folder",
            description="Output path for the masks.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="masks",
            label="Masks",
            description="Generated segmentation masks.",
            semantic="image",
            value=lambda attr: desc.Node.internalFolder + "<VIEW_ID>.exr" if not attr.node.keepFilename.value else desc.Node.internalFolder + "<FILESTEM>.exr",
            group="",
        ),
    ]
