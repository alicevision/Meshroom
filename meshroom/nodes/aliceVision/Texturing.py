from meshroom.core import desc

class Texturing(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_texturing --ini {mvsConfigValue} {allParams}'
    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    mvsConfig = desc.File(
            label='MVS Configuration file',
            description='',
            value='',
            uid=[0],
            isOutput=False,
            group='',
            )

    output = desc.File(
            label='Output Folder',
            description='Folder for output mesh: OBJ, material and texture files.',
            value='{cache}/{nodeType}/{uid0}/',
            uid=[0],
            isOutput=True,
            )

    inputMesh = desc.File(
            label='Other Input Mesh',
            description='Optional input mesh to texture. By default, it will texture the result of the reconstruction.',
            value='',
            uid=[0],
            isOutput=False,
            )

    textureSide = desc.IntParam(
            label='Texture Side',
            description='''Output texture size''',
            value=8192,
            range=(1024, 16384, 1024),
            uid=[0],
            )
    padding = desc.IntParam(
            label='Padding',
            description='''Texture edge padding size in pixel''',
            value=15,
            range=(0, 100, 1),
            uid=[0],
            )
    downscale = desc.IntParam(
            label='Downscale',
            description='''Texture downscale factor''',
            value=2,
            range=(0, 16, 1),
            uid=[0],
            )
    flipNormals = desc.BoolParam(
            label='Flip Normals',
            description='''Option to flip face normals. It can be needed as it depends on the vertices order in triangles and the convention change from one software to another.''',
            value=False,
            uid=[0],
            )

