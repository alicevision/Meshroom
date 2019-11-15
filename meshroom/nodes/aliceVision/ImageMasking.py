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
        desc.ChoiceParam(
            name='algorithm',
            label='Algorithm',
            description='',
            value='hsv',
            values=['hsv'],
            exclusive=True,
            uid=[0],
        ),
        desc.GroupAttribute(
            name="hsv",
            label="HSV Parameters",
            description="",
            formatter=desc.GroupAttribute.prefixFormatter,
            joinChar='-',
            groupDesc=[
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
            desc.FloatParam(
                name='minSaturation',
                label='Min Saturation',
                description='Hue is meaningless if saturation is low. Do not mask pixels below this threshold.',
                value=0.3,
                range=(0, 1, 0.01),
                uid=[0]
            ),
            desc.FloatParam(
                name='maxSaturation',
                label='Max Saturation',
                description='Do not mask pixels above this threshold. It might be useful to mask white/black pixels.',
                value=1,
                range=(0, 1, 0.01),
                uid=[0]
            ),
            desc.FloatParam(
                name='minValue',
                label='Min Value',
                description='Hue is meaningless if value is low. Do not mask pixels below this threshold.',
                value=0.3,
                range=(0, 1, 0.01),
                uid=[0]
            ),
            desc.FloatParam(
                name='maxValue',
                label='Max Value',
                description='Do not mask pixels above this threshold. It might be useful to mask white/black pixels.',
                value=1,
                range=(0, 1, 0.01),
                uid=[0]
            ),
        ]),
        desc.BoolParam(
            name='invert',
            label='Invert',
            description='Invert the selected area.',
            value=False,
            uid=[0]
        ),
        desc.IntParam(
            name='growRadius',
            label='Grow Radius',
            description='Grow the selected area. It might be used to fill the holes: then use shrinkRadius to restore the initial coutours.',
            value=0,
            range=(0, 50, 1),
            uid=[0]
        ),
        desc.IntParam(
            name='shrinkRadius',
            label='Shrink Radius',
            description='Shrink the selected area.',
            value=0,
            range=(0, 50, 1),
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
