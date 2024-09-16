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
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="imagesFolder",
                label="Images Folder",
                description="",
                value="",
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
        ),
        desc.ChoiceParam(
            name="outputFileType",
            label="Output File Type",
            description="Output file type for the undistorted images.",
            value="exr",
            values=["jpg", "png", "tif", "exr"],
            advanced=True,
        ),
        desc.BoolParam(
            name="saveMetadata",
            label="Save Metadata",
            description="Save projections and intrinsics information in images metadata (only for .exr images).",
            value=True,
            advanced=True,
        ),
        desc.BoolParam(
            name="saveMatricesTxtFiles",
            label="Save Matrices Text Files",
            description="Save projections and intrinsics information in text files.",
            value=False,
            advanced=True,
        ),
        desc.BoolParam(
            name="evCorrection",
            label="Correct Images Exposure",
            description="Apply a correction on images' exposure value.",
            value=False,
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
            label="Images Folder",
            description="Output folder.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="undistorted",
            label="Undistorted Images",
            description="List of undistorted images.",
            semantic="image",
            value=desc.Node.internalFolder + "<VIEW_ID>.{outputFileTypeValue}",
            group="",
            advanced=True,
        ),
    ]
