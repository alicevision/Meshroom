__version__ = "1.1"

from meshroom.core import desc
from meshroom.core.utils import DESCRIBER_TYPES, VERBOSE_LEVEL


class FeatureRepeatability(desc.AVCommandLineNode):
    commandLine = 'aliceVision_samples_repeatabilityDataset {allParams}'
    size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=40)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Utils'
    documentation = '''
Compare feature/descriptor matching repeatability on some dataset with known homography motions.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input Folder",
            description="Input folder with evaluation datasets.",
            value="",
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types used to describe an image.",
            values=DESCRIBER_TYPES,
            value=["sift"],
            exclusive=False,
            joinChar=",",
        ),
        desc.ChoiceParam(
            name="describerPreset",
            label="Describer Density",
            description="Control the ImageDescriber density (low, medium, normal, high, ultra).\n"
                        "Warning: Use ULTRA only on small datasets.",
            value="normal",
            values=["low", "medium", "normal", "high", "ultra"],
        ),
        desc.ChoiceParam(
            name="describerQuality",
            label="Describer Quality",
            description="Control the ImageDescriber quality (low, medium, normal, high, ultra).",
            value="normal",
            values=["low", "medium", "normal", "high", "ultra"],
        ),
        desc.ChoiceParam(
            name="contrastFiltering",
            label="Contrast Filtering",
            description="Contrast filtering method to ignore features with too low contrast that can be considered as noise:\n"
                        " - Static: Fixed threshold.\n"
                        " - AdaptiveToMedianVariance: Based on image content analysis.\n"
                        " - NoFiltering: Disable contrast filtering.\n"
                        " - GridSortOctaves: Grid Sort but per octaves (and only per scale at the end).\n"
                        " - GridSort: Grid sort per octaves and at the end (scale * peakValue).\n"
                        " - GridSortScaleSteps: Grid sort per octaves and at the end (scale and then peakValue).\n"
                        " - NonExtremaFiltering: Filter non-extrema peakValues.",
            value="Static",
            values=["Static", "AdaptiveToMedianVariance", "NoFiltering", "GridSortOctaves", "GridSort", "GridSortScaleSteps", "GridSortOctaveSteps", "NonExtremaFiltering"],
            advanced=True,
        ),
        desc.FloatParam(
            name="relativePeakThreshold",
            label="Relative Peak Threshold",
            description="Peak threashold relative to the median of gradients.",
            value=0.01,
            range=(0.01, 1.0, 0.001),
            advanced=True,
            enabled=lambda node: (node.contrastFiltering.value == "AdaptiveToMedianVariance"),
        ),
        desc.BoolParam(
            name="gridFiltering",
            label="Grid Filtering",
            description="Enable grid filtering. Highly recommended to ensure a usable number of features.",
            value=True,
            advanced=True,
        ),
        desc.BoolParam(
            name="forceCpuExtraction",
            label="Force CPU Extraction",
            description="Use only CPU feature extraction.",
            value=True,
            invalidate=False,
            advanced=True,
        ),
        desc.IntParam(
            name="invalidate",
            label="Invalidate",
            description="Invalidate.",
            value=0,
            range=(0, 10000, 1),
            group="",
        ),
        desc.StringParam(
            name="comments",
            label="Comments",
            description="Comments.",
            value="",
            group="",
            invalidate=False,
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
            description="Output path for the features and descriptors files (*.feat, *.desc).",
            value=desc.Node.internalFolder,
        ),
    ]
