__version__ = "3.3"

from meshroom.core import desc
from meshroom.core.utils import COLORSPACES, EXR_STORAGE_DATA_TYPE, RAW_COLOR_INTERPRETATION, VERBOSE_LEVEL

import os.path


def outputImagesValueFunct(attr):
    basename = os.path.basename(attr.node.input.value)
    fileStem = os.path.splitext(basename)[0]
    inputExt = os.path.splitext(basename)[1]
    outputExt = ('.' + attr.node.extension.value) if attr.node.extension.value else None

    if inputExt in ['.abc', '.sfm']:
        fileStem = '<FILESTEM>' if attr.node.keepImageFilename.value else '<VIEW_ID>'
        # If we have an SfM in input
        return desc.Node.internalFolder + fileStem + (outputExt or '.*')

    if inputExt:
        # If we have one or multiple files in input
        return desc.Node.internalFolder + fileStem + (outputExt or inputExt)

    if '*' in fileStem:
        # The fileStem of the input param is a regular expression,
        # so even if there is no file extension,
        # we consider that the expression represents files.
        return desc.Node.internalFolder + fileStem + (outputExt or '.*')

    # No extension and no expression means that the input param is a folder path
    return desc.Node.internalFolder + '*' + (outputExt or '.*')


class ImageProcessing(desc.AVCommandLineNode):
    commandLine = 'aliceVision_imageProcessing {allParams}'
    size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=40)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Utils'
    documentation = '''
Convert or apply filtering to the input images.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file input, image filenames or regex(es) on the image file path.\n"
                        "Supported regex:\n"
                        " - '#' matches a single digit.\n"
                        " - '@' matches one or more digits.\n"
                        " - '?' matches one character.\n"
                        " - '*' matches zero character or more.",
            value="",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="inputFolder",
                label="Input Folder",
                description="Folder containing images.",
                value="",
            ),
            name="inputFolders",
            label="Input Images Folders",
            description="Use images from specific folder(s).",
        ),
        desc.ListAttribute(
            elementDesc=desc.StringParam(
                name="metadataFolder",
                label="Metadata Folder",
                description="Specific folder containing images with metadata.",
                value="",
            ),
            name="metadataFolders",
            label="Input Metadata Folders",
            description="Use images metadata from specific folder(s).",
        ),
        desc.ChoiceParam(
            name="extension",
            label="Output File Extension",
            description="Output image file extension.\n"
                        "If unset, the output file extension will match the input's if possible.",
            value="",
            values=["", "exr", "jpg", "tiff", "png"],
        ),
        desc.BoolParam(
            name="reconstructedViewsOnly",
            label="Only Reconstructed Views",
            description="Only process reconstructed views.",
            value=False,
        ),
        desc.BoolParam(
            name="keepImageFilename",
            label="Keep Image Name",
            description="Keep the original image name instead of the view name.",
            value=False,
        ),
        desc.BoolParam(
            name="reorient",
            label="Automatic Reorientation",
            description="Automatic image reorientation.",
            value=False,
        ),
        desc.BoolParam(
            name="fixNonFinite",
            label="Fix Non-Finite",
            description="Fix non-finite pixels based on neighboring pixels average.",
            value=False,
        ),
        desc.BoolParam(
            name="exposureCompensation",
            label="Exposure Compensation",
            description="Exposure compensation (only valid for SfMData).",
            value=False,
        ),
        desc.BoolParam(
            name="rawAutoBright",
            label="RAW Auto Bright",
            description="Enable automatic exposure adjustment for RAW images.",
            value=False,
        ),
        desc.FloatParam(
            name="rawExposureAdjust",
            label="RAW Exposure Adjustment",
            description="Manual exposure adjustment in fstops for RAW images.",
            value=0.0,
            range=(-2.0, 3.0, 0.125),
        ),
        desc.GroupAttribute(
            name="lensCorrection",
            label="Lens Correction",
            description="Automatic lens correction settings.",
            joinChar=":",
            groupDesc=[
                desc.BoolParam(
                    name="lensCorrectionEnabled",
                    label="Enable",
                    description="Enable lens correction.",
                    value=False,
                ),
                desc.BoolParam(
                    name="geometry",
                    label="Geometry",
                    description="Geometry correction if a model is available in the SfMData.",
                    value=False,
                    enabled=lambda node: node.lensCorrection.lensCorrectionEnabled.value,
                ),
                desc.BoolParam(
                    name="vignetting",
                    label="Vignetting",
                    description="Vignetting correction if the model parameters are available in the metadata.",
                    value=False,
                    enabled=lambda node: node.lensCorrection.lensCorrectionEnabled.value,
                ),
                desc.BoolParam(
                    name="chromaticAberration",
                    label="Chromatic Aberration",
                    description="Chromatic aberration (fringing) correction if the model parameters are available in the metadata.",
                    value=False,
                    enabled=lambda node: node.lensCorrection.lensCorrectionEnabled.value,
                ),
            ],
        ),
        desc.FloatParam(
            name="scaleFactor",
            label="Scale Factor",
            description="Scale factor.",
            value=1.0,
            range=(0.0, 1.0, 0.01),
        ),
        desc.IntParam(
            name="maxWidth",
            label="Max Width",
            description="Maximum width of the output images (0: ignored).",
            value=0,
            range=(0, 10000, 1),
        ),
        desc.IntParam(
            name="maxHeight",
            label="Max Height",
            description="Maximum height of the output images (0: ignored).",
            value=0,
            range=(0, 10000, 1),
        ),
        desc.FloatParam(
            name="contrast",
            label="Contrast",
            description="Contrast.",
            value=1.0,
            range=(0.0, 100.0, 0.1),
        ),
        desc.IntParam(
            name="medianFilter",
            label="Median Filter",
            description="Median filter.",
            value=0,
            range=(0, 10, 1),
        ),
        desc.BoolParam(
            name="fillHoles",
            label="Fill Holes",
            description="Fill holes based on the alpha channel.\n"
                        "Note: It will enable 'fixNonFinite', as it is required for the image pyramid construction used to fill holes.",
            value=False,
        ),
        desc.GroupAttribute(
            name="sharpenFilter",
            label="Sharpen Filter",
            description="Sharpen filter parameters.",
            joinChar=":",
            groupDesc=[
                desc.BoolParam(
                    name="sharpenFilterEnabled",
                    label="Enable",
                    description="Use sharpen filter.",
                    value=False,
                ),
                desc.IntParam(
                    name="width",
                    label="Width",
                    description="Sharpening width.",
                    value=3,
                    range=(1, 9, 2),
                    enabled=lambda node: node.sharpenFilter.sharpenFilterEnabled.value,
                ),
                desc.FloatParam(
                    name="contrast",
                    label="Contrast",
                    description="Sharpening contrast.",
                    value=1.0,
                    range=(0.0, 100.0, 0.1),
                    enabled=lambda node: node.sharpenFilter.sharpenFilterEnabled.value,
                ),
                desc.FloatParam(
                    name="threshold",
                    label="Threshold",
                    description="Sharpening threshold.",
                    value=0.0,
                    range=(0.0, 1.0, 0.01),
                    enabled=lambda node: node.sharpenFilter.sharpenFilterEnabled.value,
                ),
            ],
        ),
        desc.GroupAttribute(
            name="bilateralFilter",
            label="Bilateral Filter",
            description="Bilateral filter parameters.",
            joinChar=":",
            groupDesc=[
                desc.BoolParam(
                    name="bilateralFilterEnabled",
                    label="Enable",
                    description="Use bilateral filter.",
                    value=False,
                ),
                desc.IntParam(
                    name="bilateralFilterDistance",
                    label="Distance",
                    description="Diameter of each pixel neighborhood that is used during bilateral filtering.\n"
                                "Could be very slow for large filters, so it is recommended to use 5.",
                    value=0,
                    range=(0, 9, 1),
                    enabled=lambda node: node.bilateralFilter.bilateralFilterEnabled.value,
                ),
                desc.FloatParam(
                    name="bilateralFilterSigmaSpace",
                    label="Sigma Coordinate Space",
                    description="Bilateral filter sigma in the coordinate space.",
                    value=0.0,
                    range=(0.0, 150.0, 0.01),
                    enabled=lambda node: node.bilateralFilter.bilateralFilterEnabled.value,
                ),
                desc.FloatParam(
                    name="bilateralFilterSigmaColor",
                    label="Sigma Color Space",
                    description="Bilateral filter sigma in the color space.",
                    value=0.0,
                    range=(0.0, 150.0, 0.01),
                    enabled=lambda node: node.bilateralFilter.bilateralFilterEnabled.value,
                ),
            ],
        ),
        desc.GroupAttribute(
            name="claheFilter",
            label="Clahe Filter",
            description="Clahe filter parameters.",
            joinChar=":",
            groupDesc=[
                desc.BoolParam(
                    name="claheEnabled",
                    label="Enable",
                    description="Use Contrast Limited Adaptive Histogram Equalization (CLAHE) filter.",
                    value=False,
                ),
                desc.FloatParam(
                    name="claheClipLimit",
                    label="Clip Limit",
                    description="Threshold for contrast limiting.",
                    value=4.0,
                    range=(0.0, 8.0, 1.0),
                    enabled=lambda node: node.claheFilter.claheEnabled.value,
                ),
                desc.IntParam(
                    name="claheTileGridSize",
                    label="Tile Grid Size",
                    description="Size of the grid for histogram equalization.\n"
                                "Input image will be divided into equally sized rectangular tiles.",
                    value=8,
                    range=(4, 64, 4),
                    enabled=lambda node: node.claheFilter.claheEnabled.value,
                ),
            ],
        ),
        desc.GroupAttribute(
            name="noiseFilter",
            label="Noise Filter",
            description="Noise filter parameters.",
            joinChar=":",
            groupDesc=[
                desc.BoolParam(
                    name="noiseEnabled",
                    label="Enable",
                    description="Add noise.",
                    value=False,
                ),
                desc.ChoiceParam(
                    name="noiseMethod",
                    label="Method",
                    description="There are several noise types to choose from:\n"
                                " - uniform: adds noise values uniformly distributed on range [A,B).\n"
                                " - gaussian: adds Gaussian (normal distribution) noise values with mean value A and standard deviation B.\n"
                                " - salt: changes to value A a portion of pixels given by B.\n",
                    value="uniform",
                    values=["uniform", "gaussian", "salt"],
                    enabled=lambda node: node.noiseFilter.noiseEnabled.value,
                ),
                desc.FloatParam(
                    name="noiseA",
                    label="A",
                    description="Parameter that has a different interpretation depending on the chosen method:\n"
                                " - uniform: lower bound of the range on which the noise is uniformly distributed.\n"
                                " - gaussian: the mean value of the Gaussian noise.\n"
                                " - salt: the value of the specified portion of pixels.",
                    value=0.0,
                    range=(0.0, 1.0, 0.0001),
                    enabled=lambda node: node.noiseFilter.noiseEnabled.value,
                ),
                desc.FloatParam(
                    name="noiseB",
                    label="B",
                    description="Parameter that has a different interpretation depending on the chosen method:\n"
                                " - uniform: higher bound of the range on which the noise is uniformly distributed.\n"
                                " - gaussian: the standard deviation of the Gaussian noise.\n"
                                " - salt: the portion of pixels to set to a specified value.",
                    value=1.0,
                    range=(0.0, 1.0, 0.0001),
                    enabled=lambda node: node.noiseFilter.noiseEnabled.value,
                ),
                desc.BoolParam(
                    name="noiseMono",
                    label="Mono",
                    description="If selected, a single noise value will be applied to all channels.\n"
                                "Otherwise, a separate noise value will be computed for each channel.",
                    value=True,
                    enabled=lambda node: node.noiseFilter.noiseEnabled.value,
                ),
            ],
        ),
        desc.GroupAttribute(
            name="nlmFilter",
            label="NL Means Denoising (8 bits)",
            description="NL Means Denoising Parameters.\n"
                        "This implementation only works on 8-bit images, so the colors can be reduced and clamped.",
            joinChar=":",
            groupDesc=[
                desc.BoolParam(
                    name="nlmFilterEnabled",
                    label="Enable",
                    description="Use Non-Local Mean Denoising from OpenCV to denoise images.",
                    value=False,
                ),
                desc.FloatParam(
                    name="nlmFilterH",
                    label="H",
                    description="Parameter regulating the filter strength for the luminance component.\n"
                                "Bigger H value perfectly removes noise but also removes image details,\n"
                                "smaller H value preserves details but also preserves some noise.",
                    value=5.0,
                    range=(1.0, 1000.0, 0.01),
                    enabled=lambda node: node.nlmFilter.nlmFilterEnabled.value,
                ),
                desc.FloatParam(
                    name="nlmFilterHColor",
                    label="HColor",
                    description="Parameter regulating filter strength for color components. Not necessary for grayscale images.\n"
                                "Bigger HColor value perfectly removes noise but also removes image details,\n"
                                "smaller HColor value preserves details but also preserves some noise.",
                    value=10.0,
                    range=(0.0, 1000.0, 0.01),
                    enabled=lambda node: node.nlmFilter.nlmFilterEnabled.value,
                ),
                desc.IntParam(
                    name="nlmFilterTemplateWindowSize",
                    label="Template Window Size",
                    description="Size in pixels of the template patch that is used to compute weights. Should be odd.",
                    value=7,
                    range=(1, 101, 2),
                    enabled=lambda node: node.nlmFilter.nlmFilterEnabled.value,
                ),
                desc.IntParam(
                    name="nlmFilterSearchWindowSize",
                    label="Search Window Size",
                    description="Size in pixels of the window that is used to compute weighted average for a given pixel.\n"
                                "Should be odd. Affect performance linearly: greater searchWindowsSize - greater denoising time.",
                    value=21,
                    range=(1, 1001, 2),
                    enabled=lambda node: node.nlmFilter.nlmFilterEnabled.value,
                ),
            ],
        ),
        desc.GroupAttribute(
            name="parFilter",
            label="Pixel Aspect Ratio",
            description="Pixel Aspect Ratio parameters.",
            joinChar=":",
            groupDesc=[
                desc.BoolParam(
                    name="parEnabled",
                    label="Enable",
                    description="Apply pixel aspect ratio.",
                    value=False,
                ),
                desc.BoolParam(
                    name="parRowDecimation",
                    label="Row decimation",
                    description="If selected, reduce image height by decimating the number of rows.\n"
                                "Otherwise, increase width by upsampling image columns.",
                    value=False,
                    enabled=lambda node: node.parFilter.parEnabled.value,
                ),
            ],
        ),
        desc.ChoiceParam(
            name="outputFormat",
            label="Output Image Format",
            description="Allows you to choose the format of the output image.",
            value="rgba",
            values=["rgba", "rgb", "grayscale"],
        ),
        desc.ChoiceParam(
            name="inputColorSpace",
            label="Input Color Space",
            description="Allows you to force the color space of the input image.",
            values=COLORSPACES,
            value="AUTO",
        ),
        desc.ChoiceParam(
            name="outputColorSpace",
            label="Output Color Space",
            description="Allows you to choose the color space of the output image.",
            values=COLORSPACES,
            value="AUTO",
        ),
        desc.ChoiceParam(
            name="workingColorSpace",
            label="Working Color Space",
            description="Allows you to choose the color space in which the data are processed.",
            values=COLORSPACES,
            value="Linear",
            enabled=lambda node: not node.applyDcpMetadata.value,
        ),
        desc.ChoiceParam(
            name="rawColorInterpretation",
            label="RAW Color Interpretation",
            description="Allows you to choose how RAW data are color processed.",
            values=RAW_COLOR_INTERPRETATION,
            value="DCPLinearProcessing" if os.environ.get("ALICEVISION_COLOR_PROFILE_DB", "") else "LibRawWhiteBalancing",
        ),
        desc.BoolParam(
            name="applyDcpMetadata",
            label="Apply DCP Metadata",
            description="If the image contains some DCP metadata, then generate a DCP profile from them and apply it to the image content.",
            value=False,
        ),
        desc.File(
            name="colorProfileDatabase",
            label="Color Profile Database",
            description="Color profile database directory path.",
            value="${ALICEVISION_COLOR_PROFILE_DB}",
            invalidate=False,
            enabled=lambda node: (node.rawColorInterpretation.value == "DCPLinearProcessing") or (node.rawColorInterpretation.value == "DCPMetadata"),
        ),
        desc.BoolParam(
            name="errorOnMissingColorProfile",
            label="Error On Missing DCP Color Profile",
            description="If a color profile database is specified but no color profile is found for at least one image, then an error is thrown.",
            value=True,
            enabled=lambda node: (node.rawColorInterpretation.value == "DCPLinearProcessing") or (node.rawColorInterpretation.value == "DCPMetadata"),
        ),
        desc.BoolParam(
            name="useDCPColorMatrixOnly",
            label="Use DCP Color Matrix Only",
            description="Use only the Color Matrix information from the DCP and ignore the Forward Matrix.",
            value=True,
            enabled=lambda node: (node.rawColorInterpretation.value == "DCPLinearProcessing") or (node.rawColorInterpretation.value == "DCPMetadata"),
        ),
        desc.BoolParam(
            name="doWBAfterDemosaicing",
            label="WB After Demosaicing",
            description="Do White Balance after demosaicing, just before DCP profile application.",
            value=False,
            enabled=lambda node: (node.rawColorInterpretation.value == "DCPLinearProcessing") or (node.rawColorInterpretation.value == "DCPMetadata"),
        ),
        desc.ChoiceParam(
            name="demosaicingAlgo",
            label="Demosaicing Algorithm",
            description="LibRaw demosaicing algorithm to use.",
            value="AHD",
            values=["linear", "VNG", "PPG", "AHD", "DCB", "AHD-Mod", "AFD", "VCD", "Mixed", "LMMSE", "AMaZE", "DHT", "AAHD", "none"],
        ),
        desc.ChoiceParam(
            name="highlightMode",
            label="Highlight Mode",
            description="LibRaw highlight mode:\n"
                        " - 0: Clip (default)\n"
                        " - 1: Unclip\n"
                        " - 2: Blend\n"
                        " - 3-9: Rebuild",
            value=0,
            values=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        ),
        desc.FloatParam(
            name="correlatedColorTemperature",
            label="Illuminant Color Temperature",
            description="Scene illuminant color temperature in Kelvin.\n"
                        "A negative or null value indicates that the metadata information will be used.",
            value=-1.0,
            range=(-1.0, 10000.0, 1.0),
        ),
        desc.File(
            name="lensCorrectionProfileInfo",
            label="Lens Correction Profile Info",
            description="Lens Correction Profile filepath or database directory.",
            value="${ALICEVISION_LENS_PROFILE_INFO}",
            invalidate=False,
        ),
        desc.BoolParam(
            name="lensCorrectionProfileSearchIgnoreCameraModel",
            label="LCP Generic Search",
            description="The lens name and camera maker are used to match the LCP database, but the camera model is ignored.",
            value=True,
            advanced=True,
        ),
        desc.ChoiceParam(
            name="storageDataType",
            label="Storage Data Type For EXR Output",
            description="Storage image data type for EXR outputs:\n"
                        " - float: Use full floating point (32 bits per channel).\n"
                        " - half: Use half float (16 bits per channel).\n"
                        " - halfFinite: Use half float, but clamp values to avoid non-finite values.\n"
                        " - auto: Use half float if all values can fit, else use full float.",
            values=EXR_STORAGE_DATA_TYPE,
            value="float",
        ),
        desc.ChoiceParam(
            name="exrCompressionMethod",
            label="EXR Compression Method",
            description="Compression method for EXR output images.",
            value="auto",
            values=["none", "auto", "rle", "zip", "zips", "piz", "pxr24", "b44", "b44a", "dwaa", "dwab"],
        ),
        desc.IntParam(
            name="exrCompressionLevel",
            label="EXR Compression Level",
            description="Level of compression for EXR images. The range depends on the used method.\n"
                        "For the zip/zips methods, values must be between 1 and 9.\n"
                        "A value of 0 will be ignored, and the default value for the selected method will be used.",
            value=0,
            range=(0, 500, 1),
            enabled=lambda node: node.exrCompressionMethod.value in ["dwaa", "dwab", "zip", "zips"],
        ),
        desc.BoolParam(
            name="jpegCompress",
            label="JPEG Compress",
            description="Enable JPEG compression.",
            value=True,
        ),
        desc.IntParam(
            name="jpegQuality",
            label="JPEG Quality",
            description="JPEG images quality after compression.",
            value=90,
            range=(0, 100, 1),
            enabled=lambda node: node.jpegCompress.value,
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
            description="Output SfMData file.",
            value=lambda attr: (desc.Node.internalFolder + os.path.basename(attr.node.input.value)) if (os.path.splitext(attr.node.input.value)[1] in [".abc", ".sfm"]) else "",
            group="",  # do not export on the command line
        ),
        desc.File(
            name="output",
            label="Folder",
            description="Output images folder.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="outputImages",
            label="Images",
            description="Output images.",
            semantic="image",
            value=outputImagesValueFunct,
            group="",  # do not export on the command line
        ),
    ]
