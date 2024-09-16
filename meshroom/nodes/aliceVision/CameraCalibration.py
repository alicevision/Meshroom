__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class CameraCalibration(desc.AVCommandLineNode):
    commandLine = 'aliceVision_cameraCalibration {allParams}'

    category = 'Utils'
    documentation = '''
    '''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="Input images in one of the following form:\n"
                        " - folder containing images.\n"
                        " - image sequence like \"/path/to/seq.@.jpg\".\n"
                        " - video file.",
            value="",
        ),
        desc.ChoiceParam(
            name="pattern",
            label="Pattern",
            description="Type of pattern (CHESSBOARD, CIRCLES, ASYMMETRIC_CIRCLES, ASYMMETRIC_CCTAG).",
            value="CHESSBOARD",
            values=["CHESSBOARD", "CIRCLES", "ASYMMETRIC_CIRCLES", "ASYMMETRIC_CCTAG"],
        ),
        desc.GroupAttribute(
            name="size",
            label="Size",
            description="Number of inner corners per one of board dimension like W H.",
            groupDesc=[
                desc.IntParam(
                    name="width",
                    label="Width",
                    description="",
                    value=7,
                    range=(0, 10000, 1),
                ),
                desc.IntParam(
                    name="height",
                    label="Height",
                    description="",
                    value=5,
                    range=(0, 10000, 1),
                ),
            ],
        ),
        desc.FloatParam(
            name="squareSize",
            label="Square Size",
            description="Size of the grid's square cells (mm).",
            value=1.0,
            range=(0.0, 100.0, 1.0),
        ),
        desc.IntParam(
            name="nbDistortionCoef",
            label="Nb Distortion Coef",
            description="Number of distortion coefficients.",
            value=3,
            range=(0, 5, 1),
        ),
        desc.IntParam(
            name="maxFrames",
            label="Max Frames",
            description="Maximum number of frames to extract from the video file.",
            value=0,
            range=(0, 5, 1),
        ),
        desc.IntParam(
            name="maxCalibFrames",
            label="Max Calib Frames",
            description="Maximum number of frames to use to calibrate from the selected frames.",
            value=100,
            range=(0, 1000, 1),
        ),
        desc.IntParam(
            name="calibGridSize",
            label="Calib Grid Size",
            description="Define the number of cells per edge.",
            value=10,
            range=(0, 50, 1),
        ),
        desc.IntParam(
            name="minInputFrames",
            label="Min Input Frames",
            description="Minimum number of frames to limit the refinement loop.",
            value=10,
            range=(0, 100, 1),
        ),
        desc.FloatParam(
            name="maxTotalAvgErr",
            label="Max Total Avg Err",
            description="Maximum total average error.",
            value=0.10000000000000001,
            range=(0.0, 1.0, 0.01),
        ),
        desc.File(
            name="debugRejectedImgFolder",
            label="Debug Rejected Img Folder",
            description="Folder to export images that were deleted during the refinement loop.",
            value="",
        ),
        desc.File(
            name="debugSelectedImgFolder",
            label="Debug Selected Img Folder",
            description="Folder to export debug images.",
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
            description="Output filename for intrinsic [and extrinsic] parameters.",
            value=desc.Node.internalFolder + "/cameraCalibration.cal",
        ),
    ]
