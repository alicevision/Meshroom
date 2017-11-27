from meshroom.core import desc


class Texturing(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_texturing {allParams}'
    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    inputs = [
        desc.File(
            name='ini',
            label='MVS Configuration file',
            description='',
            value='',
            uid=[0],
        ),
        desc.File(
            name='inputDenseReconstruction',
            label='Input Dense Reconstruction',
            description='Path to the dense reconstruction result (mesh with per vertex visibility).',
            value='',
            uid=[0],
        ),
        desc.File(
            name='inputMesh',
            label='Other Input Mesh',
            description='Optional input mesh to texture. By default, it will texture the result of the reconstruction.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='textureSide',
            label='Texture Side',
            description='''Output texture size''',
            value=8192,
            values=(1024, 2048, 4096, 8192, 16384),
            exclusive=True,
            uid=[0],
        ),
        desc.IntParam(
            name='padding',
            label='Padding',
            description='''Texture edge padding size in pixel''',
            value=15,
            range=(0, 100, 1),
            uid=[0],
        ),
        desc.ChoiceParam(
            name='downscale',
            label='Downscale',
            description='''Texture downscale factor''',
            value=2,
            values=(1, 2, 4, 8),
            exclusive=True,
            uid=[0],
        ),
        desc.BoolParam(
            name='flipNormals',
            label='Flip Normals',
            description='''Option to flip face normals. It can be needed as it depends on the vertices order in triangles and the convention change from one software to another.''',
            value=False,
            uid=[0],
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output Folder',
            description='Folder for output mesh: OBJ, material and texture files.',
            value='{cache}/{nodeType}/{uid0}/',
            uid=[],
        ),
        desc.File(
            name='outputMesh',
            label='Output Mesh',
            description='Folder for output mesh: OBJ, material and texture files.',
            value='{cache}/{nodeType}/{uid0}/texturedMesh.obj',
            uid=[],
            group='',
            ),
        desc.File(
            name='outputMaterial',
            label='Output Material',
            description='Folder for output mesh: OBJ, material and texture files.',
            value='{cache}/{nodeType}/{uid0}/texturedMesh.mtl',
            uid=[],
            group='',
            ),
        desc.File(
            name='outputTextures',
            label='Output Textures',
            description='Folder for output mesh: OBJ, material and texture files.',
            value='{cache}/{nodeType}/{uid0}/texture_*.png',
            uid=[],
            group='',
            ),
    ]
