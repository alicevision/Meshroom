__version__ = "3.0"

from meshroom.core import desc

import os.path

def outputImagesValueFunct(attr):
    basename = os.path.basename(attr.node.input.value)
    fileStem = os.path.splitext(basename)[0]
    inputExt = os.path.splitext(basename)[1]
    outputExt =  ('.' + attr.node.extension.value) if attr.node.extension.value else None

    if inputExt in ['.abc', '.sfm']:
        # If we have an SfM in input
        return desc.Node.internalFolder + '*' + (outputExt or '.*')

    if inputExt:
        # if we have one or multiple files in input
        return desc.Node.internalFolder + fileStem + (outputExt or inputExt)

    if '*' in fileStem:
        # The fileStem of the input param is a regular expression,
        # so even if there is no file extension,
        # we consider that the expression represents files.
        return desc.Node.internalFolder + fileStem + (outputExt or '.*')

    # No extension and no expression means that the input param is a folder path
    return desc.Node.internalFolder + '*' + (outputExt or '.*')


class ImageProcessing(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_imageProcessing {allParams}'
    size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=40)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Utils'
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
                name="inputFolder",
                label="input Folder",
                description="",
                value="",
                uid=[0],
            ),
            name="inputFolders",
            label="Images input Folders",
            description='Use images from specific folder(s).',
        ),
        desc.ListAttribute(
            elementDesc=desc.StringParam(
                name="metadataFolder",
                label="Metadata Folder",
                description="",
                value="",
                uid=[0],
            ),
            name="metadataFolders",
            label="Metadata input Folders",
            description='Use images metadata from specific folder(s).',
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
            name='fixNonFinite',
            label='Fix Non-Finite',
            description='Fix non-finite pixels based on neighboring pixels average.',
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
            label='Fill Holes',
            description='Fill holes based on the alpha channel.\n'
                        'Note: It will enable fixNonFinite, as it is required for the image pyramid construction used to fill holes.',
            value=False,
            uid=[0],
        ),
        desc.GroupAttribute(name="sharpenFilter", label="Sharpen Filter", description="Sharpen Filtering Parameters.", joinChar=":", groupDesc=[
            desc.BoolParam(
                name='sharpenFilterEnabled',
                label='Enable',
                description='Use sharpen.',
                value=False,
                uid=[0],
            ),
            desc.IntParam(
                name='width',
                label='Width',
                description='Sharpen Width.',
                value=3,
                range=(1, 9, 2),
                uid=[0],
                enabled=lambda node: node.sharpenFilter.sharpenFilterEnabled.value,
            ),
            desc.FloatParam(
                name='contrast',
                label='Contrast',
                description='Sharpen Contrast.',
                value=1.0,
                range=(0.0, 100.0, 0.1),
                uid=[0],
                enabled=lambda node: node.sharpenFilter.sharpenFilterEnabled.value,
            ),
            desc.FloatParam(
                name='threshold',
                label='Threshold',
                description='Sharpen Threshold.',
                value=0.0,
                range=(0.0, 1.0, 0.01),
                uid=[0],
                enabled=lambda node: node.sharpenFilter.sharpenFilterEnabled.value,
            ),
        ]),
        desc.GroupAttribute(name="bilateralFilter", label="Bilateral Filter", description="Bilateral Filtering Parameters.", joinChar=":", groupDesc=[
            desc.BoolParam(
                name='bilateralFilterEnabled',
                label='Enable',
                description='Bilateral Filter.',
                value=False,
                uid=[0],
            ),
            desc.IntParam(
                name='bilateralFilterDistance',
                label='Distance',
                description='Diameter of each pixel neighborhood that is used during bilateral filtering.\nCould be very slow for large filters, so it is recommended to use 5.',
                value=0,
                range=(0, 9, 1),
                uid=[0],
                enabled=lambda node: node.bilateralFilter.bilateralFilterEnabled.value,
            ),
            desc.FloatParam(
                name='bilateralFilterSigmaSpace',
                label='Sigma Coordinate Space',
                description='Bilateral Filter sigma in the coordinate space.',
                value=0.0,
                range=(0.0, 150.0, 0.01),
                uid=[0],
                enabled=lambda node: node.bilateralFilter.bilateralFilterEnabled.value,
            ),
            desc.FloatParam(
                name='bilateralFilterSigmaColor',
                label='Sigma Color Space',
                description='Bilateral Filter sigma in the color space.',
                value=0.0,
                range=(0.0, 150.0, 0.01),
                uid=[0],
                enabled=lambda node: node.bilateralFilter.bilateralFilterEnabled.value,
            ),
        ]),
        desc.GroupAttribute(name="claheFilter", label="Clahe Filter", description="Clahe Filtering Parameters.", joinChar=":", groupDesc=[
            desc.BoolParam(
                name='claheEnabled',
                label='Enable',
                description='Use Contrast Limited Adaptive Histogram Equalization (CLAHE) Filter.',
                value=False,
                uid=[0],
            ),
            desc.FloatParam(
                name='claheClipLimit',
                label='Clip Limit',
                description='Sets Threshold For Contrast Limiting.',
                value=4.0,
                range=(0.0, 8.0, 1.0),
                uid=[0],
                enabled=lambda node: node.claheFilter.claheEnabled.value,
            ),
            desc.IntParam(
                name='claheTileGridSize',
                label='Tile Grid Size',
                description='Sets Size Of Grid For Histogram Equalization. Input Image Will Be Divided Into Equally Sized Rectangular Tiles.',
                value=8,
                range=(4, 64, 4),
                uid=[0],
                enabled=lambda node: node.claheFilter.claheEnabled.value,
            ),
        ]),
        desc.GroupAttribute(name="noiseFilter", label="Noise Filter", description="Noise Filtering Parameters.", joinChar=":", groupDesc=[
            desc.BoolParam(
                name='noiseEnabled',
                label='Enable',
                description='Add Noise.',
                value=False,
                uid=[0],
            ),
            desc.ChoiceParam(
                name='noiseMethod',
                label='Method',
                description=" * method: There are several noise types to choose from:\n"
                            " * uniform: adds noise values uninformly distributed on range [A,B).\n"
                            " * gaussian: adds Gaussian (normal distribution) noise values with mean value A and standard deviation B.\n"
                            " * salt: changes to value A a portion of pixels given by B.\n",
                value='uniform',
                values=['uniform', 'gaussian', 'salt'],
                exclusive=True,
                uid=[0],
                enabled=lambda node: node.noiseFilter.noiseEnabled.value,
            ),
            desc.FloatParam(
                name='noiseA',
                label='A',
                description='Parameter that have a different interpretation depending on the method chosen.',
                value=0.0,
                range=(0.0, 1.0, 0.0001),
                uid=[0],
                enabled=lambda node: node.noiseFilter.noiseEnabled.value,
            ),
            desc.FloatParam(
                name='noiseB',
                label='B',
                description='Parameter that have a different interpretation depending on the method chosen.',
                value=1.0,
                range=(0.0, 1.0, 0.0001),
                uid=[0],
                enabled=lambda node: node.noiseFilter.noiseEnabled.value,
            ),
            desc.BoolParam(
                name='noiseMono',
                label='Mono',
                description='If is Checked, a single noise value will be applied to all channels otherwise a separate noise value will be computed for each channel.',
                value=True,
                uid=[0],
                enabled=lambda node: node.noiseFilter.noiseEnabled.value,
            ),
        ]),
        desc.ChoiceParam(
                name='outputFormat',
                label='Output Image Format',
                description='Allows you to choose the format of the output image.',
                value='rgba',
                values=['rgba', 'rgb', 'grayscale'],
                exclusive=True,
                uid=[0],
        ),
        desc.ChoiceParam(
            name='storageDataType',
            label='Storage Data Type for EXR output',
            description='Storage image data type:\n'
                        ' * float: Use full floating point (32 bits per channel)\n'
                        ' * half: Use half float (16 bits per channel)\n'
                        ' * halfFinite: Use half float, but clamp values to avoid non-finite values\n'
                        ' * auto: Use half float if all values can fit, else use full float\n',
            value='float',
            values=['float', 'half', 'halfFinite', 'auto'],
            exclusive=True,
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
            value=lambda attr: (desc.Node.internalFolder + os.path.basename(attr.node.input.value)) if (os.path.splitext(attr.node.input.value)[1] in ['.abc', '.sfm']) else '',
            uid=[],
            group='',  # do not export on the command line
        ),
        desc.File(
            name='output',
            label='Output Folder',
            description='Output Images Folder.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='outputImages',
            label='Output Images',
            description='Output Image Files.',
            value= outputImagesValueFunct,
            group='',  # do not export on the command line
            uid=[],
        ),
    ]
