__version__ = "1.1"

from meshroom.core import desc


class ImageProcessing(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_imageProcessing {allParams}'
    size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=40)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentation = '''
Convert or apply filtering to the input images.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file input, image filenames or regex(es) on the image file path.\nsupported regex: \'#\' matches a single digit, \'@\' one or more digits, \'?\' one character and \'*\' zero or more.',
            value='',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name="imagesFolder",
                label="Images Folder",
                description="",
                value="",
                uid=[0],
            ),
            name="inputFolders",
            label="Images input Folders",
            description='Use images from specific folder(s).',
        ),
        desc.ChoiceParam(
            name='extension',
            label='Output File Extension',
            description='Output Image File Extension.',
            value='',
            values=['', 'exr', 'jpg', 'tiff', 'png'],
            exclusive=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='reconstructedViewsOnly',
            label='Only Reconstructed Views',
            description='Process Only Reconstructed Views',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='keepImageFilename',
            label='Keep Image Filename',
            description='Keep Image Filename instead of using View UID.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='exposureCompensation',
            label='Exposure Compensation',
            description='Exposure Compensation',
            value=False,
            uid=[0],
        ),
        desc.FloatParam(
            name='scaleFactor',
            label='ScaleFactor',
            description='Scale Factor.',
            value=1.0,
            range=(0.0, 1.0, 0.01),
            uid=[0],
        ),
        desc.FloatParam(
            name='contrast',
            label='Contrast',
            description='Contrast.',
            value=1.0,
            range=(0.0, 100.0, 0.1),
            uid=[0],
        ),
        desc.IntParam(
            name='medianFilter',
            label='Median Filter',
            description='Median Filter.',
            value=0,
            range=(0, 10, 1),
            uid=[0],
        ),
        desc.BoolParam(
            name='fillHoles',
            label='Fill holes',
            description='Fill holes.',
            value=False,
            uid=[0],
        ),
        desc.IntParam(
            name='sharpenWidth',
            label='Sharpen Width',
            description='Sharpen Width.',
            value=1,
            range=(1, 9, 2),
            uid=[0],
        ),
        desc.FloatParam(
            name='sharpenContrast',
            label='Sharpen Contrast',
            description='Sharpen Contrast.',
            value=1.0,
            range=(0.0, 100.0, 0.1),
            uid=[0],
        ),
        desc.FloatParam(
            name='sharpenThreshold',
            label='Sharpen Threshold',
            description='Sharpen Threshold.',
            value=0.0,
            range=(0.0, 1.0, 0.01),
            uid=[0],
        ),
        desc.BoolParam(
            name='bilateralFilter',
            label='Bilateral Filter',
            description='Bilateral Filter.',
            value=False,
            uid=[0],
        ),
        desc.IntParam(
            name='bilateralFilterDistance',
            label='Bilateral Filter Distance',
            description='Diameter of each pixel neighborhood that is used during bilateral filtering.\nCould be very slow for large filters, so it is recommended to use 5.',
            value=0,
            range=(0, 9, 1),
            uid=[0],
        ),
        desc.FloatParam(
            name='bilateralFilterSigmaSpace',
            label='Bilateral Filter Sigma Space',
            description='Bilateral Filter sigma in the coordinate space.',
            value=0.0,
            range=(0.0, 150.0, 0.01),
            uid=[0],
        ),
        desc.FloatParam(
            name='bilateralFilterSigmaColor',
            label='Bilateral Filter Sigma Color Space',
            description='Bilateral Filter sigma in the color space.',
            value=0.0,
            range=(0.0, 150.0, 0.01),
            uid=[0],
        ),
        desc.BoolParam(
            name='claheFilter',
            label='Clahe Filter',
            description='Use Contrast Limited Adaptive Histogram Equalization (CLAHE) Filter.',
            value=False,
            uid=[0],
        ),
        desc.FloatParam(
            name='claheClipLimit',
            label='Clahe Clip Limit.',
            description='Sets Threshold For Contrast Limiting.',
            value=4.0,
            range=(0.0, 8.0, 1.0),
            uid=[0],
        ),
        desc.IntParam(
            name='claheTileGridSize',
            label='Clahe Tile Grid Size.',
            description='Sets Size Of Grid For Histogram Equalization. Input Image Will Be Divided Into Equally Sized Rectangular Tiles.',
            value=8,
            range=(4, 64, 4),
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name='outSfMData',
            label='Output sfmData',
            description='Output sfmData.',
            value=desc.Node.internalFolder + 'sfmData.abc',
            uid=[],
        ),
        desc.File(
            name='outputFolder',
            label='Output Images Folder',
            description='Output Images Folder.',
            value=desc.Node.internalFolder,
            group='',  # do not export on the command line
            uid=[],
        ),
    ]
