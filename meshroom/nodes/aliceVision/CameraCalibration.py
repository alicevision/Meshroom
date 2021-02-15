__version__ = "1.0"

from meshroom.core import desc


class CameraCalibration(desc.CommandLineNode):
    commandLine = 'aliceVision_cameraCalibration {allParams}'

    category = 'Utils'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''Input images in one of the following form:
 - folder containing images
 - image sequence like "/path/to/seq.@.jpg"
 - video file''',
            value='',
            uid=[0],
            ),
        desc.ChoiceParam(
            name='pattern',
            label='Pattern',
            description='''Type of pattern (CHESSBOARD, CIRCLES, ASYMMETRIC_CIRCLES, ASYMMETRIC_CCTAG).''',
            value='CHESSBOARD',
            values=['CHESSBOARD', 'CIRCLES', 'ASYMMETRIC_CIRCLES', 'ASYMMETRIC_CCTAG'],
            exclusive=True,
            uid=[0],
            ),
        desc.GroupAttribute(name="size", label="Size", description="Number of inner corners per one of board dimension like W H.", groupDesc=[
            desc.IntParam(
                name='width',
                label='Width',
                description='',
                value=7,
                range=(0, 10000, 1),
                uid=[0],
                ),
            desc.IntParam(
                name='height',
                label='Height',
                description='',
                value=5,
                range=(0, 10000, 1),
                uid=[0],
                ),
            ]),
        desc.FloatParam(
            name='squareSize',
            label='Square Size',
            description='''Size of the grid's square cells (mm).''',
            value=1.0,
            range=(0.0, 100.0, 1.0),
            uid=[0],
            ),
        desc.IntParam(
            name='nbDistortionCoef',
            label='Nb Distortion Coef',
            description='''Number of distortion coefficient.''',
            value=3,
            range=(0, 5, 1),
            uid=[0],
            ),
        desc.IntParam(
            name='maxFrames',
            label='Max Frames',
            description='''Maximal number of frames to extract from the video file.''',
            value=0,
            range=(0, 5, 1),
            uid=[0],
            ),
        desc.IntParam(
            name='maxCalibFrames',
            label='Max Calib Frames',
            description='''Maximal number of frames to use to calibrate from the selected frames.''',
            value=100,
            range=(0, 1000, 1),
            uid=[0],
            ),
        desc.IntParam(
            name='calibGridSize',
            label='Calib Grid Size',
            description='''Define the number of cells per edge.''',
            value=10,
            range=(0, 50, 1),
            uid=[0],
            ),
        desc.IntParam(
            name='minInputFrames',
            label='Min Input Frames',
            description='''Minimal number of frames to limit the refinement loop.''',
            value=10,
            range=(0, 100, 1),
            uid=[0],
            ),
        desc.FloatParam(
            name='maxTotalAvgErr',
            label='Max Total Avg Err',
            description='''Max Total Average Error.''',
            value=0.10000000000000001,
            range=(0.0, 1.0, 0.01),
            uid=[0],
            ),
        desc.File(
            name='debugRejectedImgFolder',
            label='Debug Rejected Img Folder',
            description='''Folder to export delete images during the refinement loop.''',
            value='',
            uid=[0],
            ),
        desc.File(
            name='debugSelectedImgFolder',
            label='Debug Selected Img Folder',
            description='''Folder to export debug images.''',
            value='',
            uid=[0],
            ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''Output filename for intrinsic [and extrinsic] parameters.''',
            value=desc.Node.internalFolder + '/cameraCalibration.cal',
            uid=[],
            ),
    ]
