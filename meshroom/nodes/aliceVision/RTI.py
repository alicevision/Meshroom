__version__ = "3.0"

from meshroom.core import desc

class RTI(desc.CommandLineNode):
    commandLine = 'aliceVision_rti_PS {allParams}'
    category = 'Photometry'
    documentation = '''
TODO.
'''

    inputs = [
        desc.File(
            name='inputPath',
            label='SfmData',
            description='Input file. Coulb be SfMData file or folder.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='maskPath',
            label='Mask folder path',
            description='Mask folder path',
            value='',
            uid=[0],
        ),
        desc.File(
            name='pathToJSONLightFile',
            label='Lights Folder',
            description='Folder containing lighting information.',
            value='',
            uid=[0]
        ),
        desc.IntParam(
            name='HSOrder',
            label='HS order',
            description='Order of the spherical harmonics. ',
            value=0,
            range=(0, 2, 1),
            uid=[0],
            advanced=True,
         ),
         desc.BoolParam(
            name='removeAmbiant',
            label='removeAmbiant',
            description='removeAmbiant',
            value=False,
            uid=[0],
            advanced=True,
         ),
         desc.BoolParam(
            name='isRobust',
            label='isRobust',
            description='isRobust',
            value=False,
            uid=[0],
            advanced=True,
         ),
         desc.IntParam(
            name='downscale',
            label='downscale',
            description='downscale',
            value=1,
            uid=[0],
            range=(1, 2, 8),
            advanced=True
         )
    ]

    outputs = [
        desc.File(
            name='outputPath',
            label='Output path',
            description='Path to the output folder',
            value=desc.Node.internalFolder,
            uid=[],
        )
    ]