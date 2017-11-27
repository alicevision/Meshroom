from meshroom.core import desc

class Meshing(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_meshing {allParams}'

    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    inputs = [
        desc.File(
            name="ini",
            label='MVS Configuration file',
            description='',
            value='',
            uid=[0],
            ),
        desc.IntParam(
            name='maxPts',
            label='maxPts',
            description='Max points',
            value=6000000,
            range=(500000, 30000000, 1000),
            uid=[0],
        ),
        desc.IntParam(
            name='maxPtsPerVoxel',
            label='maxPtsPerVoxel',
            description='Max points per voxel',
            value=1000000,
            range=(500000, 30000000, 1000),
            uid=[0],
        ),
        desc.ChoiceParam(
            name='partitioning',
            label='Partitioning',
            description='',
            value='singleBlock',
            values=('singleBlock', 'auto'),
            exclusive=True,
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output mesh",
            description="Output mesh (OBJ file format).",
            value="{cache}/{nodeType}/{uid0}/mesh.obj",
            uid=[],
            ),
        desc.File(
            name="outputDenseReconstruction",
            label="Output reconstruction",
            description="Output dense reconstruction (BIN file format).",
            value="{cache}/{nodeType}/{uid0}/denseReconstruction.bin",
            uid=[],
            group="",
            ),
    ]
