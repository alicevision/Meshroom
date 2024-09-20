__version__ = "2.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ExportAnimatedCamera(desc.AVCommandLineNode):
    commandLine = 'aliceVision_exportAnimatedCamera {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Export'
    documentation = '''
Convert cameras from an SfM scene into an animated cameras in Alembic file format.
Based on the input image filenames, it will recognize the input video sequence to create an animated camera.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="SfMData file containing a complete SfM.",
            value="",
        ),
        desc.File(
            name="sfmDataFilter",
            label="SfMData Filter",
            description="Filter out cameras from the export if they are part of this SfMData.\n"
                        "If empty, export all cameras.",
            value="",
        ),
        desc.File(
            name="viewFilter",
            label="View Filter",
            description="Select the cameras to export using an expression based on the image filepath.\n"
                        "If empty, export all cameras.",
            value="",
        ),
        desc.BoolParam(
            name="exportSTMaps",
            label="Export ST Maps",
            description="Export ST maps. Motion (x, y) is encoded in the image channels to correct the lens distortion.\n"
                        "It represents the absolute pixel positions of an image normalized between 0 and 1.",
            value=True,
        ),
        desc.BoolParam(
            name="exportUndistortedImages",
            label="Export Undistorted Images",
            description="Export undistorted images.",
            value=False,
        ),
        desc.ChoiceParam(
            name="undistortedImageType",
            label="Undistort Image Format",
            description="Image file format to use for undistorted images ('jpg', 'png', 'tif', 'exr (half)').",
            value="exr",
            values=["jpg", "png", "tif", "exr"],
            enabled=lambda node: node.exportUndistortedImages.value,
        ),
        desc.BoolParam(
            name="exportFullROD",
            label="Export Full ROD",
            description="Export full ROD.",
            value=False,
            enabled=lambda node: node.exportUndistortedImages.value and node.undistortedImageType.value == "exr",
        ),
        desc.BoolParam(
            name="correctPrincipalPoint",
            label="Correct Principal Point",
            description="Correct principal point.",
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
            label="Folder",
            description="Output folder with animated camera and undistorted images.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="outputCamera",
            label="Camera",
            description="Output filename for the animated camera in Alembic format.",
            value=desc.Node.internalFolder + "camera.abc",
            group="",  # exclude from command line
        ),
        desc.File(
            name="outputUndistorted",
            label="Undistorted Folder",
            description="Output undistorted folder.",
            value=desc.Node.internalFolder + "undistort/",
            group="",  # exclude from command line
        ),
        desc.File(
            name="outputImages",
            label="Undistorted Images",
            description="Output undistorted images.",
            value=desc.Node.internalFolder + "undistort/" + "<INTRINSIC_ID>_<FILESTEM>.{undistortedImageTypeValue}",
            semantic="image",
            group="",  # exclude from command line
            enabled=lambda node: node.exportUndistortedImages.value,
        ),
    ]
