from meshroom.core import desc

class MeshResampling(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_meshing {allParams}'

    cpu = desc.Level.NORMAL
    ram = desc.Level.NORMAL

    inputs = [
        desc.File(
            name="intput",
            label='Input Mesh (OBJ file format).',
            description='',
            value='',
            uid=[0],
            ),
        desc.FloatParam(
            name='simplificationFactor',
            label='Simplification factor',
            description='Simplification factor',
            value=0.5,
            range=(0.0, 1.0, 0.01),
            uid=[0],
        ),
        desc.IntParam(
            name='nbVertices',
            label='Fixed Number of Vertices',
            description='Fixed number of output vertices.',
            value=0.0,
            range=(0.0, 1.0, 0.01),
            uid=[0],
        ),
        desc.IntParam(
            name='minVertices',
            label='Min Vertices',
            description='Min number of output vertices.',
            value=0.0,
            range=(0.0, 1.0, 0.01),
            uid=[0],
        ),
        desc.IntParam(
            name='maxVertices',
            label='Max Vertices',
            description='Max number of output vertices.',
            value=0.0,
            range=(0.0, 1.0, 0.01),
            uid=[0],
        ),
        desc.IntParam(
            name='nbLloydIter',
            label='Number of Pre-Smoothing Iteration',
            description='Number of iterations for Lloyd pre-smoothing.',
            value=40,
            range=(0, 100, 1),
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output mesh",
            description="Output mesh (OBJ file format).",
            value='{cache}/{nodeType}/{uid0}/mesh.obj',
            uid=[],
            ),
    ]
