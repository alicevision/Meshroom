__version__ = "3.0"

from meshroom.core import desc


class SphereDetection(desc.CommandLineNode):
    commandLine = 'aliceVision_sphereDetection {allParams}'
    category = 'Photometry'
    documentation = '''
TODO.
'''

    inputs = [
        desc.File(
            name='input_sfmdata_path',
            label='SfmData',
            description='Input file. Coulb be SfMData file or folder.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='input_model_path',
            label='input_model_path',
            description='Input file. Coulb be SfMData file or folder.',
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='autoDetect',
            label='autoDetect',
            description='autoDetect',
            value=False,
            uid=[0],
        ),
        desc.GroupAttribute(
            name="sphereCenter",
            label="Sphere Center",
            description="Center of the circle (XY offset to the center in pixels).",
            groupDesc=[
                desc.FloatParam(
                    name="x", label="x", description="X Offset in pixels",
                    value=0.0,
                    uid=[0],
                    range=(-1000.0, 10000.0, 1.0)),
                desc.FloatParam(
                    name="y", label="y", description="Y Offset in pixels",
                    value=0.0,
                    uid=[0],
                    range=(-1000.0, 10000.0, 1.0)),
                ],
            group=None, # skip group from command line
        ),
        desc.FloatParam(
            name='sphereRadius',
            label='r',
            description='Sphere radius in pixels.',
            value=500.0,
            range=(0.0, 1000.0, 0.1),
            uid=[0],
        )
    ]

    outputs = [
        desc.File(
            name='output_path',
            label='Output json file',
            description='Light information will be written here.',
            value=desc.Node.internalFolder,
            uid=[],
        )
    ]
