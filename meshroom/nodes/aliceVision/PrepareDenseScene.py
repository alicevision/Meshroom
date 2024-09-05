__version__ = "3.1"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class PrepareDenseScene(desc.AVCommandLineNode):
    commandLine = 'aliceVision_prepareDenseScene {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=40)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Dense Reconstruction'
    documentation = '''
This node export undistorted images so the depth map and texturing can be computed on Pinhole images without distortion.
'''

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
            invalidate=True,
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="imagesFolder",
                label="Images Folder",
                description="",
                value="",
                invalidate=True,
            ),
            name="imagesFolders",
            label="Images Folders",
            description="Use images from specific folder(s). Filename should be the same or the image UID.",
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="masksFolder",
                label="Masks Folder",
                description="",
                value="",
                invalidate=True,
            ),
            name="masksFolders",
            label="Masks Folders",
            description="Use masks from specific folder(s). Filename should be the same or the image UID.",
        ),
        desc.ChoiceParam(
            name="maskExtension",
            label="Mask Extension",
            description="File extension for the masks to use.",
            value="png",
            values=["exr", "jpg", "png"],
            exclusive=True,
            invalidate=True,
        ),
        desc.ChoiceParam(
            name="outputFileType",
            label="Output File Type",
            description="Output file type for the undistorted images.",
            value="exr",
            values=["jpg", "png", "tif", "exr"],
            exclusive=True,
            invalidate=True,
            advanced=True,
        ),
        desc.BoolParam(
            name="saveMetadata",
            label="Save Metadata",
            description="Save projections and intrinsics information in images metadata (only for .exr images).",
            value=True,
            invalidate=True,
            advanced=True,
        ),
        desc.BoolParam(
            name="saveMatricesTxtFiles",
            label="Save Matrices Text Files",
            description="Save projections and intrinsics information in text files.",
            value=False,
            invalidate=True,
            advanced=True,
        ),
        desc.BoolParam(
            name="evCorrection",
            label="Correct Images Exposure",
            description="Apply a correction on images' exposure value.",
            value=False,
            invalidate=True,
            advanced=True,
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
            exclusive=True,
            invalidate=False,
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Images Folder",
            description="Output folder.",
            value=desc.Node.internalFolder,
            invalidate=False,
        ),
        desc.File(
            name="undistorted",
            label="Undistorted Images",
            description="List of undistorted images.",
            semantic="image",
            value=desc.Node.internalFolder + "<VIEW_ID>.{outputFileTypeValue}",
            invalidate=False,
            group="",
            advanced=True,
        ),
    ]
