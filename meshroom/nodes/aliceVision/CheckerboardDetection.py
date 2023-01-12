__version__ = "1.0"

from meshroom.core import desc


class CheckerboardDetection(desc.AVCommandLineNode):
    commandLine = 'aliceVision_checkerboardDetection {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=5)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Other'
    documentation = '''
This node detects checkerboard structures in a set of images.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData File',
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='useNestedGrids',
            label='Nested calibration grid',
            description='Images contain nested calibration grids. These grids must be centered on image center.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='doubleSize',
            label='Double Size',
            description='Double the image size prior to processing',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='exportDebugImages',
            label='Export Debug Images',
            description='Export Debug Images',
            value=False,
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Folder',
            description='',
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='checkerLines',
            enabled= lambda node: node.exportDebugImages.value,
            label='Checker Lines',
            description='Debug Images.',
            semantic='image',
            value=desc.Node.internalFolder + 'checker_<VIEW_ID>.png',
            group='',  # do not export on the command line
            uid=[],
        ),
    ]
