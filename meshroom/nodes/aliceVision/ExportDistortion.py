__version__ = "1.0"

from meshroom.core import desc

class ExportDistortion(desc.AVCommandLineNode):
    commandLine = 'aliceVision_exportDistortion {allParams}'

    category = 'Export'
    documentation = '''
Export the lens distortion model as Nuke node and STMaps.
It also allows to export an undistorted image of the lens grids for validation.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
            uid=[0],
        ),
        desc.BoolParam(
            name="exportNukeNode",
            label="Export Nuke Node",
            description="Export Nuke LensDistortion node as nuke file.\n"
                        "Only supports 3DEqualizer/3DE4 Anamorphic lens model.",
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name="exportLensGridsUndistorted",
            label="Export Lens Grids Undistorted",
            description="Export the lens grids undistorted for validation.",
            value=True,
            uid=[0],
        ),
        desc.BoolParam(
            name="exportSTMaps",
            label="Export STMaps",
            description="Export STMaps for distortion and undistortion.",
            value=True,
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Folder",
            description="Output folder.",
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name="distortionNukeNode",
            label="Distortion Nuke Node",
            description="Calibrated distortion ST map.",
            value=desc.Node.internalFolder + "nukeLensDistortion_<INTRINSIC_ID>.nk",
            group="",  # do not export on the command line
            uid=[],
            enabled=lambda node: node.exportNukeNode.value,
        ),
        desc.File(
            name="lensGridsUndistorted",
            label="Undistorted Lens Grids",
            description="Undistorted lens grids for validation",
            semantic="image",
            value=desc.Node.internalFolder + "lensgrid_<VIEW_ID>_undistort.exr",
            group="",  # do not export on the command line
            uid=[],
            enabled=lambda node: node.exportLensGridsUndistorted.value,
        ),
        desc.File(
            name="distortionStMap",
            label="Distortion ST Map",
            description="Calibrated distortion ST map.",
            semantic="image",
            value=desc.Node.internalFolder + "stmap_<INTRINSIC_ID>_distort.exr",
            group="",  # do not export on the command line
            uid=[],
            enabled=lambda node: node.exportSTMaps.value,
        ),
        desc.File(
            name="undistortionStMap",
            label="Undistortion ST Map",
            description="Calibrated undistortion ST map.",
            semantic="image",
            value=desc.Node.internalFolder + "stmap_<INTRINSIC_ID>_undistort.exr",
            group="",  # do not export on the command line
            uid=[],
            enabled=lambda node: node.exportSTMaps.value,
        ),
    ]
