__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class ExportDistortion(desc.AVCommandLineNode):
    commandLine = "aliceVision_exportDistortion {allParams}"

    category = "Export"
    documentation = """
Export the lens distortion model as Nuke node and STMaps.
It also allows to export an undistorted image of the lens grids for validation.
"""

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.BoolParam(
            name="exportNukeNode",
            label="Export Nuke Node",
            description="Export Nuke LensDistortion node as nuke file.\n"
                        "Only supports 3DEqualizer lens models.",
            value=True,
        ),
        desc.BoolParam(
            name="exportAnimatedNukeNode",
            label="Export Animated Nuke Node",
            description="Export animated distortion for this sequence as nuke file.",
            value=False,
        ),
        desc.BoolParam(
            name="exportLensGridsUndistorted",
            label="Export Lens Grids Undistorted",
            description="Export the lens grids undistorted for validation.",
            value=True,
        ),
        desc.BoolParam(
            name="exportSTMaps",
            label="Export STMaps",
            description="Export STMaps for distortion and undistortion.",
            value=True,
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
            description="Output folder.",
            value=desc.Node.internalFolder,
        ),
        desc.File(
            name="distortionNukeNode",
            label="Distortion Nuke Node",
            description="Calibrated distortion ST map.",
            value=desc.Node.internalFolder + "nukeLensDistortion_<INTRINSIC_ID>.nk",
            group="",  # do not export on the command line
            enabled=lambda node: node.exportNukeNode.value,
        ),
        desc.File(
            name="lensGridsUndistorted",
            label="Undistorted Lens Grids",
            description="Undistorted lens grids for validation",
            semantic="image",
            value=desc.Node.internalFolder + "lensgrid_<VIEW_ID>_undistort.exr",
            group="",  # do not export on the command line
            enabled=lambda node: node.exportLensGridsUndistorted.value,
        ),
        desc.File(
            name="distortionStMap",
            label="Distortion ST Map",
            description="Calibrated distortion ST map.",
            semantic="image",
            value=desc.Node.internalFolder + "stmap_<INTRINSIC_ID>_distort.exr",
            group="",  # do not export on the command line
            enabled=lambda node: node.exportSTMaps.value,
        ),
        desc.File(
            name="undistortionStMap",
            label="Undistortion ST Map",
            description="Calibrated undistortion ST map.",
            semantic="image",
            value=desc.Node.internalFolder + "stmap_<INTRINSIC_ID>_undistort.exr",
            group="",  # do not export on the command line
            enabled=lambda node: node.exportSTMaps.value,
        ),
    ]
