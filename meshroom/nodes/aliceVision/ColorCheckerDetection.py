__version__ = "1.0"

from meshroom.core import desc

import os.path


class ColorCheckerDetection(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_colorCheckerDetection {allParams}'
    size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=40)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentation = '''
(BETA) \\
Performs Macbeth color checker chart detection.

Outputs:
- the detected color charts position and colors
- the associated tranform matrix from "theoric" to "measured" 
assuming that the "theoric" Macbeth chart corners coordinates are: 
(0, 0), (1675, 0), (1675, 1125), (0, 1125)
  
Dev notes:
- Fisheye/pinhole is not handled
- ColorCheckerViewer is unstable with multiple color chart within a same image
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file input, image filenames or regex(es) on the image file path.\nsupported regex: \'#\' matches a single digit, \'@\' one or more digits, \'?\' one character and \'*\' zero or more.',
            value='',
            uid=[0],
        ),
        desc.IntParam(
            name='maxCount',
            label='Max count by image',
            description='Max color charts count to detect in a single image',
            value=1,
            range=(1, 3, 1),
            uid=[0],
            advanced=True,
        ),
        desc.BoolParam(
            name='debug',
            label='Debug',
            description='If checked, debug data will be generated',
            value=False,
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='outputData',
            label='Color checker data',
            description='Output position and colorimetric data extracted from detected color checkers in the images',
            value=desc.Node.internalFolder + '/ccheckers.json',
            uid=[],
        ),
    ]
