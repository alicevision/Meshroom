__version__ = "1.3"

from meshroom.core import desc
from meshroom.core.utils import COLORSPACES, DESCRIBER_TYPES, VERBOSE_LEVEL


class FeatureExtraction(desc.AVCommandLineNode):
    commandLine = 'aliceVision_featureExtraction {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=40)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Sparse Reconstruction'
    documentation = '''
This node extracts distinctive groups of pixels that are, to some extent, invariant to changing camera viewpoints during image acquisition.
Hence, a feature in the scene should have similar feature descriptions in all images.

This node implements multiple methods:
 * **SIFT**
The most standard method. This is the default and recommended value for all use cases.
 * **AKAZE**
AKAZE can be interesting solution to extract features in challenging condition. It could be able to match wider angle than SIFT but has drawbacks.
It may extract too many features, the repartition is not always good.
It is known to be good on challenging surfaces such as skin.
 * **CCTAG**
CCTag is a marker type with 3 or 4 crowns. You can put markers in the scene during the shooting session to automatically re-orient and re-scale the scene to a known size.
It is robust to motion-blur, depth-of-field, occlusion. Be careful to have enough white margin around your CCTags.


## Online
[https://alicevision.org/#photogrammetry/natural_feature_extraction](https://alicevision.org/#photogrammetry/natural_feature_extraction)
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="masksFolder",
            label="Masks Folder",
            description="Use masks to filter features. Filename should be the same or the image UID.",
            value="",
        ),
        desc.ChoiceParam(
            name="maskExtension",
            label="Mask Extension",
            description="File extension for masks.",
            value="png",
            values=["png", "exr", "jpg"],
        ),
        desc.BoolParam(
            name="maskInvert",
            label="Invert Masks",
            description="Invert mask values.",
            value=False,
        ),
        desc.ChoiceParam(
            name="describerTypes",
            label="Describer Types",
            description="Describer types used to describe an image.",
            values=DESCRIBER_TYPES,
            value=["dspsift"],
            exclusive=False,
            joinChar=",",
            exposed=True,
        ),
        desc.ChoiceParam(
            name="describerPreset",
            label="Describer Density",
            description="Control the ImageDescriber density (low, medium, normal, high, ultra).\n"
                        "Warning: Use ULTRA only on small datasets.",
            value="normal",
            values=["low", "medium", "normal", "high", "ultra", "custom"],
            group=lambda node: 'allParams' if node.describerPreset.value != 'custom' else None,
        ),
        desc.IntParam(
            name="maxNbFeatures",
            label="Max Nb Features",
            description="Maximum number of features extracted (0 means default value based on Describer Density).",
            value=0,
            range=(0, 100000, 1000),
            advanced=True,
            enabled=lambda node: (node.describerPreset.value == "custom"),
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
                        " - NonExtremaFiltering: Filter non-extrema peakValues.\n",
            value="GridSort",
            values=["Static", "AdaptiveToMedianVariance", "NoFiltering", "GridSortOctaves", "GridSort", "GridSortScaleSteps", "GridSortOctaveSteps", "NonExtremaFiltering"],
            advanced=True,
        ),
        desc.FloatParam(
            name="relativePeakThreshold",
            label="Relative Peak Threshold",
            description="Peak threshold relative to median of gradients.",
            value=0.01,
            range=(0.01, 1.0, 0.001),
            advanced=True,
            enabled=lambda node: (node.contrastFiltering.value == "AdaptiveToMedianVariance"),
        ),
        desc.BoolParam(
            name="gridFiltering",
            label="Grid Filtering",
            description="Enable grid filtering. Highly recommended to ensure usable number of features.",
            value=True,
            advanced=True,
        ),
        desc.ChoiceParam(
            name="workingColorSpace",
            label="Working Color Space",
            description="Allows you to choose the color space in which the data are processed.",
            values=COLORSPACES,
            value="sRGB",
        ),
        desc.BoolParam(
            name="forceCpuExtraction",
            label="Force CPU Extraction",
            description="Use only CPU feature extraction.",
            value=True,
            advanced=True,
        ),
        desc.IntParam(
            name="maxThreads",
            label="Max Nb Threads",
            description="Maximum number of threads to run simultaneously (0 for automatic mode).",
            value=0,
            range=(0, 24, 1),
            invalidate=False,
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
            label="Features Folder",
            description="Output path for the features and descriptors files (*.feat, *.desc).",
            value=desc.Node.internalFolder,
        ),
    ]
