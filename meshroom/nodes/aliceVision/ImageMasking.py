__version__ = "3.0"

from meshroom.core import desc


class ImageMasking(desc.CommandLineNode):
    commandLine = 'aliceVision_imageMasking {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=40)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
        ),
        #desc.GroupAttribute(
        #    name="colour",
        #    label="Keyed Colour",
        #    description="",
        #    groupDesc=[
        #        desc.FloatParam(name="r", label="r", description="", value=0, uid=[0], range=(0, 1, 0.01)),
        #        desc.FloatParam(name="g", label="g", description="", value=0, uid=[0], range=(0, 1, 0.01)),
        #        desc.FloatParam(name="b", label="b", description="", value=0, uid=[0], range=(0, 1, 0.01)),
        #    ]),
        desc.ChoiceParam(
            name='algorithm',
            label='Algorithm',
            description='',
            value='hsv',
            values=['hsv'],
            exclusive=True,
            uid=[0],
        ),
        desc.FloatParam(
            name='hue',
            label='Hue',
            description='Hue value to isolate in [0,1] range. 0 = red, 0.33 = green, 0.66 = blue, 1 = red.',
            value=0.33,
            range=(0, 1, 0.01),
            uid=[0]
        ),
        desc.FloatParam(
            name='hueRange',
            label='Tolerance',
            description='Tolerance around the hue value to isolate.',
            value=0.1,
            range=(0, 1, 0.01),
            uid=[0]
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''Output folder.''',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
